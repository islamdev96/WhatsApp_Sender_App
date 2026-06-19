using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using WhatsAppSender.Core.Automation;
using WhatsAppSender.Core.Data;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Services;

public class CampaignRunner
{
    private readonly IWhatsAppService _waService;
    private readonly CampaignsRepository _campaignsRepo;
    private readonly SpintaxEngine _spintaxEngine;
    private readonly SafetyService _safetyService;

    public event Action<CampaignResult>? OnMessageSent;
    public event Action<int, int>? OnProgress; // Sent count, Total count
    public event Action<string>? OnStatusChanged; // e.g. "Running", "Completed", "Stopped", "Failed"

    public CampaignRunner(
        IWhatsAppService waService,
        CampaignsRepository campaignsRepo,
        SpintaxEngine spintaxEngine,
        SafetyService safetyService)
    {
        _waService = waService;
        _campaignsRepo = campaignsRepo;
        _spintaxEngine = spintaxEngine;
        _safetyService = safetyService;
    }

    public async Task RunCampaignAsync(
        Campaign campaign,
        List<Contact> contacts,
        string messageTemplate,
        string? attachmentPath,
        string? attachmentType,
        string? caption,
        bool sendTextWithImage,
        bool enableSpintax,
        int delayMin,
        int delayMax,
        CancellationToken ct)
    {
        OnStatusChanged?.Invoke("Running");
        var startTime = DateTime.Now;
        int total = contacts.Count;
        int sent = 0;
        int failed = 0;
        int invalid = 0;

        // Initialize campaign in database to get ID
        campaign.Date = startTime.ToString("yyyy-MM-dd HH:mm:ss");
        campaign.Total = total;
        campaign.Sent = 0;
        campaign.Failed = 0;
        campaign.Invalid = 0;
        campaign.SuccessRate = 0.0;

        int dbCampaignId = _campaignsRepo.CreateCampaign(campaign);
        campaign.Id = dbCampaignId;

        try
        {
            for (int i = 0; i < contacts.Count; i++)
            {
                if (ct.IsCancellationRequested)
                {
                    OnStatusChanged?.Invoke("Stopped");
                    break;
                }

                var contact = contacts[i];

                // 1. Personalize message using variables (e.g., {name})
                var personalized = messageTemplate.Replace("{name}", contact.Name ?? string.Empty);
                var finalMsg = enableSpintax ? _spintaxEngine.Parse(personalized) : personalized;

                // 2. Personalize caption if applicable
                var finalCaption = string.IsNullOrEmpty(caption) ? string.Empty : caption.Replace("{name}", contact.Name ?? string.Empty);
                finalCaption = enableSpintax ? _spintaxEngine.Parse(finalCaption) : finalCaption;

                // 3. Send message via WhatsApp service
                var statusStr = await _waService.SendMessageAsync(
                    contact.Phone,
                    finalMsg,
                    attachmentPath,
                    attachmentType,
                    finalCaption,
                    sendTextWithImage,
                    ct);

                // 4. Determine status result
                string status = "Failed";
                string errorCode = string.Empty;

                if (statusStr == "SUCCESS")
                {
                    status = "Sent";
                    sent++;
                }
                else if (statusStr == "INVALID")
                {
                    status = "Invalid";
                    invalid++;
                }
                else if (statusStr == "STOPPED")
                {
                    OnStatusChanged?.Invoke("Stopped");
                    break;
                }
                else
                {
                    status = "Failed";
                    errorCode = statusStr;
                    failed++;
                }

                var result = new CampaignResult
                {
                    CampaignId = dbCampaignId,
                    Phone = contact.Phone,
                    Name = contact.Name ?? string.Empty,
                    Status = status,
                    ErrorCode = errorCode,
                    Timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
                };

                // Save individual result (updates campaign stats in db in real-time)
                _campaignsRepo.AddCampaignResult(result);
                OnMessageSent?.Invoke(result);
                OnProgress?.Invoke(i + 1, total);

                // 5. Apply safety delay unless it's the last message
                if (i < contacts.Count - 1)
                {
                    var baseDelayMs = _safetyService.GetNextDelayMs(delayMin, delayMax);
                    double extraDelaySec = 0;
                    if (!string.IsNullOrEmpty(attachmentPath) && File.Exists(attachmentPath))
                    {
                        extraDelaySec = _safetyService.ExtraDelayAfterAttachment(attachmentType ?? "document", attachmentPath);
                    }

                    var totalDelayMs = baseDelayMs + (int)(extraDelaySec * 1000);
                    await Task.Delay(totalDelayMs, ct);
                }
            }

            OnStatusChanged?.Invoke("Completed");
        }
        catch (OperationCanceledException)
        {
            OnStatusChanged?.Invoke("Stopped");
        }
        catch (Exception)
        {
            OnStatusChanged?.Invoke("Failed");
            throw;
        }
        finally
        {
            // Update final duration
            var duration = (int)(DateTime.Now - startTime).TotalSeconds;
            _campaignsRepo.UpdateCampaignDuration(dbCampaignId, duration);
        }
    }
}
