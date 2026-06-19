using System;
using System.Threading;
using System.Threading.Tasks;

namespace WhatsAppSender.Core.Automation;

public interface IWhatsAppService
{
    event Action<string, string, string?>? OnDiagnosticLog; // Level, Message, Detail
    Task InitializeAsync(string profileName, bool useProxy, string proxyHost, string proxyPort, string proxyUsername, string proxyPassword, string userAgent);
    Task<bool> IsLoggedInAsync();
    Task<bool> OpenChatAsync(string phone, CancellationToken ct);
    Task<string> SendMessageAsync(string phone, string message, string? attachmentPath, string? attachmentType, string? caption, bool sendTextWithImage, CancellationToken ct);
    Task<bool> CheckNumberExistsAsync(string phone, CancellationToken ct);
    void Close();
}
