using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using WhatsAppSender.Core.Data;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Services;

public class SchedulerService
{
    private readonly ScheduledCampaignsRepository _scheduledRepo;
    private readonly ContactsRepository _contactsRepo;
    private readonly CancellationTokenSource _cts = new();
    private Task? _pollingTask;
    private Func<ScheduledCampaign, List<Contact>, Task<bool>>? _callback;

    public event Action<string, string>? OnLog; // Level, Message

    public SchedulerService(ScheduledCampaignsRepository scheduledRepo, ContactsRepository contactsRepo)
    {
        _scheduledRepo = scheduledRepo;
        _contactsRepo = contactsRepo;
    }

    public void Start(Func<ScheduledCampaign, List<Contact>, Task<bool>> callback)
    {
        _callback = callback;
        if (_pollingTask == null || _pollingTask.IsCompleted)
        {
            _pollingTask = Task.Run(PollLoopAsync);
            OnLog?.Invoke("INFO", "Scheduler polling service started.");
        }
    }

    public void Stop()
    {
        _cts.Cancel();
        try
        {
            _pollingTask?.Wait(TimeSpan.FromSeconds(2));
        }
        catch { }
        OnLog?.Invoke("INFO", "Scheduler polling service stopped.");
    }

    private async Task PollLoopAsync()
    {
        var ct = _cts.Token;
        while (!ct.IsCancellationRequested)
        {
            try
            {
                var nowStr = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
                var upcoming = _scheduledRepo.GetUpcomingPending();

                foreach (var sc in upcoming)
                {
                    // If the scheduled time is less than or equal to now, trigger it
                    if (string.Compare(sc.ScheduledTime, nowStr) <= 0)
                    {
                        OnLog?.Invoke("INFO", $"Triggering scheduled campaign ID {sc.Id} (Scheduled: {sc.ScheduledTime})");

                        // Mark as sending to avoid double triggering
                        _scheduledRepo.UpdateStatus(sc.Id, "sending");

                        // Resolve contacts list
                        List<Contact> contacts = new();
                        if (!string.IsNullOrEmpty(sc.GroupName))
                        {
                            var group = _contactsRepo.GetByName(sc.GroupName);
                            if (group != null && group.Contacts != null)
                            {
                                contacts.AddRange(group.Contacts);
                            }
                        }
                        else if (!string.IsNullOrEmpty(sc.ContactsJson))
                        {
                            try
                            {
                                var parsed = JsonSerializer.Deserialize<List<Contact>>(sc.ContactsJson);
                                if (parsed != null)
                                {
                                    contacts.AddRange(parsed);
                                }
                            }
                            catch (Exception ex)
                            {
                                OnLog?.Invoke("ERROR", $"Failed to parse contacts JSON for scheduled campaign ID {sc.Id}: {ex.Message}");
                            }
                        }

                        // Run the campaign callback asynchronously
                        _ = Task.Run(async () =>
                        {
                            try
                            {
                                bool success = false;
                                if (_callback != null)
                                {
                                    success = await _callback(sc, contacts);
                                }
                                var finalStatus = success ? "completed" : "failed";
                                _scheduledRepo.UpdateStatus(sc.Id, finalStatus);
                                OnLog?.Invoke("INFO", $"Scheduled campaign ID {sc.Id} finished with status: {finalStatus}");
                            }
                            catch (Exception ex)
                            {
                                _scheduledRepo.UpdateStatus(sc.Id, "failed");
                                OnLog?.Invoke("ERROR", $"Exception executing scheduled campaign ID {sc.Id}: {ex.Message}");
                            }
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                OnLog?.Invoke("ERROR", $"Error in scheduler polling loop: {ex.Message}");
            }

            try
            {
                await Task.Delay(10000, ct); // Poll every 10 seconds
            }
            catch (TaskCanceledException)
            {
                break;
            }
        }
    }
}
