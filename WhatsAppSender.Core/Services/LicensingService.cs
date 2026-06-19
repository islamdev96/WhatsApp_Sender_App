using System;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace WhatsAppSender.Core.Services;

public class LicensingService
{
    private const string Salt = "WHATSAPP_TURBO_PRO_SECRET_SALT_2026";
    private const string KeyFile = "activation.key";

    public string GetHWID()
    {
        string uuidOut = string.Empty;
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = "/c wmic csproduct get uuid",
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            using var proc = Process.Start(psi);
            if (proc != null)
            {
                string output = proc.StandardOutput.ReadToEnd();
                proc.WaitForExit();
                var lines = output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                if (lines.Length > 1)
                {
                    uuidOut = lines[1].Trim();
                }
            }

            if (string.IsNullOrEmpty(uuidOut) || uuidOut.ToLower().Contains("uuid"))
            {
                throw new Exception("Invalid UUID returned");
            }
        }
        catch
        {
            try
            {
                uuidOut = $"{Environment.MachineName}-{Environment.GetEnvironmentVariable("PROCESSOR_IDENTIFIER")}-{Environment.UserName}";
            }
            catch
            {
                uuidOut = "OFFLINE-DESKTOP-LICENSE-HWID-KEY";
            }
        }

        string hashed = Sha256(uuidOut).ToUpperInvariant();
        return $"{hashed.Substring(0, 4)}-{hashed.Substring(4, 4)}-{hashed.Substring(8, 4)}-{hashed.Substring(12, 4)}";
    }

    public string GenerateLicenseKey(string hwid)
    {
        string cleanHwid = hwid.Trim();
        string rawStr = $"{cleanHwid}-{Salt}";
        string hashed = Sha256(rawStr).ToUpperInvariant();
        return $"WSP-{hashed.Substring(0, 4)}-{hashed.Substring(4, 4)}-{hashed.Substring(8, 4)}-{hashed.Substring(12, 4)}";
    }

    public bool VerifyStoredLicense()
    {
        if (!File.Exists(KeyFile))
        {
            return false;
        }

        try
        {
            string storedKey = File.ReadAllText(KeyFile).Trim();
            string hwid = GetHWID();
            string expected = GenerateLicenseKey(hwid);
            return storedKey == expected;
        }
        catch
        {
            return false;
        }
    }

    public bool SaveLicenseKey(string key)
    {
        string trimmedKey = key.Trim();
        string hwid = GetHWID();
        string expected = GenerateLicenseKey(hwid);
        if (trimmedKey == expected)
        {
            try
            {
                File.WriteAllText(KeyFile, trimmedKey);
                return true;
            }
            catch
            {
                return false;
            }
        }
        return false;
    }

    private static string Sha256(string input)
    {
        using var sha = SHA256.Create();
        var bytes = sha.ComputeHash(Encoding.UTF8.GetBytes(input));
        var sb = new StringBuilder();
        foreach (var b in bytes)
        {
            sb.Append(b.ToString("x2"));
        }
        return sb.ToString();
    }
}
