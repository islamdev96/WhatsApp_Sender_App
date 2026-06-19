using System;
using System.IO;
using Xunit;
using WhatsAppSender.Core.Services;

namespace WhatsAppSender.Tests;

public class CoreServicesTests
{
    [Fact]
    public void TestSpintaxEngine_BasicAndRecursive()
    {
        var engine = new SpintaxEngine();

        // Test basic spintax
        var resultBasic = engine.Parse("{Hello|Hi|Hey} user");
        Assert.True(resultBasic == "Hello user" || resultBasic == "Hi user" || resultBasic == "Hey user");

        // Test recursive spintax
        var resultRecursive = engine.Parse("{Hello {friend|brother}|Hey} greetings");
        Assert.True(resultRecursive == "Hello friend greetings" || 
                    resultRecursive == "Hello brother greetings" || 
                    resultRecursive == "Hey greetings");
        
        // Test empty string
        Assert.Equal(string.Empty, engine.Parse(string.Empty));
    }

    [Fact]
    public void TestSafetyService_NormalizeAndExtraDelay()
    {
        var safety = new SafetyService();

        // Normalize media type by extension
        Assert.Equal("image", safety.NormalizeMediaType("document", "test.jpg"));
        Assert.Equal("video", safety.NormalizeMediaType("document", "movie.mp4"));
        Assert.Equal("document", safety.NormalizeMediaType("document", "file.pdf"));

        // Force media type overrides
        Assert.Equal("image", safety.NormalizeMediaType("image", "file.pdf"));
        Assert.Equal("video", safety.NormalizeMediaType("video", "test.jpg"));

        // Extra delay calculations
        Assert.Equal(4.0, safety.ExtraDelayAfterAttachment("document", "file.pdf"));
        Assert.Equal(5.0, safety.ExtraDelayAfterAttachment("image", "test.jpg"));
        Assert.Equal(8.0, safety.ExtraDelayAfterAttachment("video", "movie.mp4")); // Since file doesn't exist, size is ignored
    }

    [Fact]
    public void TestSafetyService_AssessCampaignSettings()
    {
        var safety = new SafetyService();

        // Safe campaign settings (delay >= 80s results in <= 45 messages per hour)
        var assessment = safety.AssessCampaignSettings(
            contactCount: 10,
            delayMin: 80,
            delayMax: 120,
            batchSize: 5,
            batchPauseMin: 60,
            hasMedia: false);

        Assert.True(assessment.Ok);
        Assert.Empty(assessment.Warnings);

        // Risky settings (too fast, no delay, too many contacts)
        var riskyAssessment = safety.AssessCampaignSettings(
            contactCount: 250,
            delayMin: 5,
            delayMax: 10,
            batchSize: 5,
            batchPauseMin: 10,
            hasMedia: true);

        Assert.False(riskyAssessment.Ok);
        Assert.NotEmpty(riskyAssessment.Warnings);
        Assert.Contains(riskyAssessment.Warnings, w => w.Contains("التأخير الأدنى"));
        Assert.Contains(riskyAssessment.Warnings, w => w.Contains("استراحة الدفعة"));
        Assert.Contains(riskyAssessment.Warnings, w => w.Contains("كبير"));
    }

    [Fact]
    public void TestLicensingService_GenerateAndVerify()
    {
        var licensing = new LicensingService();

        // HWID should be stable and formatted as XXXX-XXXX-XXXX-XXXX
        var hwid = licensing.GetHWID();
        Assert.NotNull(hwid);
        Assert.Matches(@"^[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$", hwid);

        // Generate license key for current HWID
        var key = licensing.GenerateLicenseKey(hwid);
        Assert.NotNull(key);
        Assert.StartsWith("WSP-", key);

        // Verify stored license behavior (writing then verifying)
        if (File.Exists("activation.key"))
        {
            File.Delete("activation.key");
        }

        // Initially no key, so verify should return false
        Assert.False(licensing.VerifyStoredLicense());

        // Save valid key
        var saved = licensing.SaveLicenseKey(key);
        Assert.True(saved);
        Assert.True(licensing.VerifyStoredLicense());

        // Cleanup
        if (File.Exists("activation.key"))
        {
            File.Delete("activation.key");
        }
    }
}
