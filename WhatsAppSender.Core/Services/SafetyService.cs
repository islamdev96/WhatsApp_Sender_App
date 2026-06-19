using System;
using System.Collections.Generic;
using System.IO;

namespace WhatsAppSender.Core.Services;

public class CampaignAssessment
{
    public bool Ok { get; set; }
    public List<string> Warnings { get; set; } = new();
    public double SuggestedDelayMin { get; set; }
    public double SuggestedDelayMax { get; set; }
}

public class SafetyService
{
    private readonly Random _rng = new();

    // Conservative defaults matching Python (seconds)
    public const double MIN_DELAY_SECONDS = 15;
    public const double RECOMMENDED_DELAY_MIN = 30;
    public const double RECOMMENDED_DELAY_MAX = 120;
    public const double MIN_BATCH_PAUSE_SECONDS = 60;
    public const int MAX_MESSAGES_PER_HOUR_SOFT = 45;
    public const int MAX_MESSAGES_PER_SESSION_SOFT = 200;

    public string NormalizeMediaType(string attType, string path = "")
    {
        var t = (attType ?? "document").ToLower().Trim();
        var ext = string.IsNullOrEmpty(path) ? string.Empty : Path.GetExtension(path).ToLower();

        if (t == "image" || t == "video" || t == "document")
        {
            if (t != "document")
            {
                return t;
            }
        }

        if (ext == ".jpg" || ext == ".jpeg" || ext == ".png" || ext == ".gif" || ext == ".bmp" || ext == ".webp")
        {
            return "image";
        }

        if (ext == ".mp4" || ext == ".avi" || ext == ".mov" || ext == ".mkv" || ext == ".3gp" || ext == ".webm")
        {
            return "video";
        }

        return "document";
    }

    public double ExtraDelayAfterAttachment(string attType, string path = "")
    {
        var t = NormalizeMediaType(attType, path);
        if (t == "document")
        {
            return 4.0;
        }
        if (t == "video")
        {
            double baseDelay = 8.0;
            try
            {
                if (!string.IsNullOrEmpty(path) && File.Exists(path))
                {
                    double sizeMb = new FileInfo(path).Length / (1024.0 * 1024.0);
                    baseDelay += Math.Min(20.0, sizeMb * 2.0);
                }
            }
            catch
            {
                // Ignore errors reading file size
            }
            return baseDelay;
        }
        if (t == "image")
        {
            return 5.0;
        }
        return 3.0;
    }

    public int GetNextDelayMs(double minSec, double maxSec)
    {
        if (minSec < 0) minSec = 0;
        if (maxSec < minSec) maxSec = minSec;

        double delaySec = minSec + _rng.NextDouble() * (maxSec - minSec);
        return (int)(delaySec * 1000.0);
    }

    public CampaignAssessment AssessCampaignSettings(
        int contactCount,
        double delayMin,
        double delayMax,
        int batchSize,
        double batchPauseMin,
        bool hasMedia = false)
    {
        var assessment = new CampaignAssessment { Ok = true };

        if (delayMin < MIN_DELAY_SECONDS)
        {
            assessment.Warnings.Add(
                $"التأخير الأدنى ({delayMin}s) منخفض جداً — يُنصح بـ {MIN_DELAY_SECONDS}s على الأقل لتقليل مخاطر الحظر.");
            assessment.Ok = false;
        }

        if (delayMax < delayMin)
        {
            assessment.Warnings.Add("التأخير الأقصى أصغر من الأدنى — سيتم تبديلهما.");
            assessment.Ok = false;
            // Swap if invalid logic
            var temp = delayMin;
            delayMin = delayMax;
            delayMax = temp;
        }

        if (batchSize > 0 && batchPauseMin < MIN_BATCH_PAUSE_SECONDS)
        {
            assessment.Warnings.Add(
                $"استراحة الدفعة ({batchPauseMin}s) قصيرة — يُنصح بـ {MIN_BATCH_PAUSE_SECONDS}s أو أكثر.");
        }

        if (contactCount > MAX_MESSAGES_PER_SESSION_SOFT)
        {
            assessment.Warnings.Add(
                $"عدد جهات الاتصال ({contactCount}) كبير — قسّم الحملة إلى دفعات أصغر (≤{MAX_MESSAGES_PER_SESSION_SOFT}).");
        }

        if (hasMedia && delayMin < RECOMMENDED_DELAY_MIN)
        {
            assessment.Warnings.Add(
                $"إرسال وسائط يتطلب تأخيراً أطول — يُنصح بـ {RECOMMENDED_DELAY_MIN}-{RECOMMENDED_DELAY_MAX} ثانية.");
        }

        double estPerHour = delayMin > 0 ? (3600.0 / delayMin) : 999.0;
        if (estPerHour > MAX_MESSAGES_PER_HOUR_SOFT)
        {
            assessment.Warnings.Add(
                $"المعدل التقريبي (~{(int)estPerHour} رسالة/ساعة) مرتفع — الهدف الآمن: ≤{MAX_MESSAGES_PER_HOUR_SOFT}/ساعة.");
        }

        double suggestedMin = Math.Max(delayMin, MIN_DELAY_SECONDS);
        if (hasMedia)
        {
            suggestedMin = Math.Max(suggestedMin, RECOMMENDED_DELAY_MIN);
        }

        double suggestedMax = Math.Max(delayMax, suggestedMin + 10.0);
        if (hasMedia)
        {
            suggestedMax = Math.Max(suggestedMax, RECOMMENDED_DELAY_MAX);
        }
        else
        {
            suggestedMax = Math.Max(suggestedMax, suggestedMin + 30.0);
        }

        assessment.SuggestedDelayMin = suggestedMin;
        assessment.SuggestedDelayMax = suggestedMax;

        return assessment;
    }
}
