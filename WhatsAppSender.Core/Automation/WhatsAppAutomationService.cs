using System;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Web.WebView2.Core;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Automation;

public class WhatsAppAutomationService : IWhatsAppService
{
    private CoreWebView2? _coreWebView2;
    private SelectorsData _selectors = new();

    public event Action<string, string, string?>? OnDiagnosticLog;

    public class SelectorsData
    {
        public string ChatListPane { get; set; } = string.Empty;
        public string MessageInputBox { get; set; } = string.Empty;
        public string SendButton { get; set; } = string.Empty;
        public string AttachButton { get; set; } = string.Empty;
        public string FileInput { get; set; } = string.Empty;
        public string MediaInput { get; set; } = string.Empty;
        public string CaptionBox { get; set; } = string.Empty;
        public string MediaPreviewSendButton { get; set; } = string.Empty;
        public string[] InvalidNumberMarkers { get; set; } = Array.Empty<string>();
        public string InvalidNumberOkButton { get; set; } = string.Empty;
    }

    public WhatsAppAutomationService()
    {
        LoadSelectors();
    }

    private void Log(string level, string message, string? detail = null)
    {
        OnDiagnosticLog?.Invoke(level, message, detail);
    }

    private void LoadSelectors()
    {
        try
        {
            var path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "selectors.json");
            if (File.Exists(path))
            {
                var json = File.ReadAllText(path);
                _selectors = JsonSerializer.Deserialize<SelectorsData>(json) ?? new();
                Log("INFO", "Selectors loaded from selectors.json successfully.");
            }
            else
            {
                _selectors = new SelectorsData
                {
                    ChatListPane = "div[aria-label='Chat list'], #pane-side, div[data-testid='chat-list']",
                    MessageInputBox = "div[contenteditable='true'][data-tab='10'], #main footer div[contenteditable='true'][role='textbox']",
                    SendButton = "button[aria-label='Send'], button[aria-label='إرسال'], span[data-icon='send'], span[data-icon='send-light']",
                    AttachButton = "span[data-icon='attach-menu-plus'], span[data-icon*='attach'], div[title='Attach'], div[title='إرفاق']",
                    FileInput = "input[type='file'][accept='*']",
                    MediaInput = "input[type='file'][accept*='video/mp4'], input[type='file'][accept*='image']",
                    CaptionBox = "div[data-testid='media-caption-input-container'] div[contenteditable='true'], div[role='dialog'] div[contenteditable='true']",
                    MediaPreviewSendButton = "div[data-testid='media-viewer'] span[data-icon='send'], div[role='dialog'] span[data-icon='send'], div[role='dialog'] button[aria-label='Send'], div[role='dialog'] button[aria-label='إرسال']",
                    InvalidNumberMarkers = new[]
                    {
                        "phone number shared via url is invalid",
                        "Phone number shared via url is invalid",
                        "is not on WhatsApp",
                        "غير موجود على واتساب",
                        "غير صحيح",
                        "ليس لديه واتساب",
                        "ليس لديه WhatsApp"
                    },
                    InvalidNumberOkButton = "div[data-animate-modal-popup='true'] div[role='button'], button[normalize-space()='موافق'], button[normalize-space()='OK']"
                };
                Log("WARNING", "selectors.json not found. Loaded default fallback selectors.");
            }
        }
        catch (Exception ex)
        {
            Log("ERROR", $"Failed to load selectors: {ex.Message}");
        }
    }

    public Task InitializeAsync(string profileName, bool useProxy, string proxyHost, string proxyPort, string proxyUsername, string proxyPassword, string userAgent)
    {
        Log("INFO", "WhatsApp Automation Service initialized.");
        return Task.CompletedTask;
    }

    public void SetCoreWebView2(CoreWebView2 coreWebView2)
    {
        _coreWebView2 = coreWebView2;
        Log("INFO", "CoreWebView2 instance linked to automation service.");
    }

    // ── Dispatcher UI Thread Safety Marshalling Helpers ──
    private async Task<string> ExecuteScriptSafeAsync(string js)
    {
        if (_coreWebView2 == null) return string.Empty;

        var dispatcher = System.Windows.Application.Current?.Dispatcher;
        if (dispatcher == null || dispatcher.CheckAccess())
        {
            return await _coreWebView2.ExecuteScriptAsync(js);
        }
        else
        {
            return await dispatcher.InvokeAsync(async () =>
            {
                return await _coreWebView2.ExecuteScriptAsync(js);
            }).Task.Unwrap();
        }
    }

    private async Task<string> CallDevToolsProtocolMethodSafeAsync(string methodName, string parametersAsJson)
    {
        if (_coreWebView2 == null) return string.Empty;

        var dispatcher = System.Windows.Application.Current?.Dispatcher;
        if (dispatcher == null || dispatcher.CheckAccess())
        {
            return await _coreWebView2.CallDevToolsProtocolMethodAsync(methodName, parametersAsJson);
        }
        else
        {
            return await dispatcher.InvokeAsync(async () =>
            {
                return await _coreWebView2.CallDevToolsProtocolMethodAsync(methodName, parametersAsJson);
            }).Task.Unwrap();
        }
    }

    private void NavigateSafe(string url)
    {
        if (_coreWebView2 == null) return;

        var dispatcher = System.Windows.Application.Current?.Dispatcher;
        if (dispatcher == null || dispatcher.CheckAccess())
        {
            _coreWebView2.Navigate(url);
        }
        else
        {
            dispatcher.Invoke(() =>
            {
                _coreWebView2.Navigate(url);
            });
        }
    }

    public async Task<bool> IsLoggedInAsync()
    {
        if (_coreWebView2 == null) return false;

        try
        {
            var js = $"!!document.querySelector(\"{_selectors.ChatListPane.Replace("\"", "\\\"")}\")";
            var result = await ExecuteScriptSafeAsync(js);
            return result == "true";
        }
        catch (Exception ex)
        {
            Log("DEBUG", $"Error checking login status: {ex.Message}");
            return false;
        }
    }

    public async Task<bool> OpenChatAsync(string phone, CancellationToken ct)
    {
        if (_coreWebView2 == null) return false;

        Log("STEP", $"Opening chat for: {phone}");
        var url = $"https://web.whatsapp.com/send?phone={phone}";
        NavigateSafe(url);

        var start = DateTime.Now;
        var timeout = TimeSpan.FromSeconds(45);

        while (DateTime.Now - start < timeout)
        {
            ct.ThrowIfCancellationRequested();

            if (await CheckIsInvalidNumberAsync())
            {
                Log("WARN", "Invalid WhatsApp number detected.", phone);
                await DismissInvalidNumberModalAsync();
                return false;
            }

            var inputExists = await CheckSelectorExistsAsync(_selectors.MessageInputBox);
            if (inputExists)
            {
                Log("INFO", "Chat loaded and ready.", phone);
                await Task.Delay(1000, ct); // Let it settle
                return true;
            }

            await Task.Delay(500, ct);
        }

        Log("ERROR", "Timeout waiting for chat to load.", phone);
        return false;
    }

    public async Task<string> SendMessageAsync(string phone, string message, string? attachmentPath, string? attachmentType, string? caption, bool sendTextWithImage, CancellationToken ct)
    {
        if (_coreWebView2 == null) return "ERR_NOT_READY";

        try
        {
            var chatOpened = await OpenChatAsync(phone, ct);
            if (!chatOpened)
            {
                return "INVALID";
            }

            if (!string.IsNullOrEmpty(attachmentPath) && File.Exists(attachmentPath))
            {
                var attachSuccess = await SendAttachmentAsync(attachmentPath, attachmentType ?? "document", caption, sendTextWithImage ? message : null, ct);
                if (!attachSuccess)
                {
                    return "ERR_ATTACH_FAILED";
                }

                if (!string.IsNullOrEmpty(message) && !sendTextWithImage)
                {
                    await Task.Delay(2000, ct);
                    var textSuccess = await SendTextOnlyAsync(message, ct);
                    if (!textSuccess) return "ERR_TEXT_FAILED";
                }
            }
            else
            {
                if (!string.IsNullOrEmpty(message))
                {
                    var textSuccess = await SendTextOnlyAsync(message, ct);
                    if (!textSuccess) return "ERR_TEXT_FAILED";
                }
            }

            return "SUCCESS";
        }
        catch (OperationCanceledException)
        {
            return "STOPPED";
        }
        catch (Exception ex)
        {
            Log("ERROR", $"Exception sending message to {phone}: {ex.Message}");
            return $"ERR_GENERAL: {ex.Message}";
        }
    }

    public async Task<bool> CheckNumberExistsAsync(string phone, CancellationToken ct)
    {
        if (_coreWebView2 == null) return false;

        try
        {
            var chatOpened = await OpenChatAsync(phone, ct);
            return chatOpened;
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> SendTextOnlyAsync(string message, CancellationToken ct)
    {
        if (_coreWebView2 == null) return false;
        Log("STEP", "Sending text message...");

        // Pass text as safe JSON to script
        var msgJson = JsonSerializer.Serialize(message);
        var inputSel = JsonSerializer.Serialize(_selectors.MessageInputBox);
        var sendSel = JsonSerializer.Serialize(_selectors.SendButton);

        var js = $@"
        (async function() {{
            const input = document.querySelector({inputSel});
            if (!input) return 'NO_INPUT';
            input.focus();

            // Clear any existing content
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);

            // Insert text line by line with proper line breaks
            const text = {msgJson};
            const lines = text.split('\n');
            for (let i = 0; i < lines.length; i++) {{
                if (i > 0) document.execCommand('insertLineBreak');
                if (lines[i].length) document.execCommand('insertText', false, lines[i]);
            }}

            // Wait for the Send button to become enabled (up to ~3 seconds)
            for (let t = 0; t < 30; t++) {{
                const btn = document.querySelector({sendSel});
                if (btn && btn.getAttribute('aria-disabled') !== 'true' && !btn.disabled) {{
                    btn.click();
                    return 'SENT';
                }}
                await new Promise(r => setTimeout(r, 100));
            }}
            return 'BTN_DISABLED';
        }})();";

        var result = await ExecuteScriptSafeAsync(js);
        var clean = result?.Trim('"');
        if (clean == "SENT")
        {
            await Task.Delay(800, ct);
            Log("INFO", "Text message sent successfully.");
            return true;
        }

        Log("ERROR", $"Failed to send text. Reason: {clean}");
        return false;
    }

    private async Task<bool> SendAttachmentAsync(string filePath, string fileType, string? caption, string? captionOverride, CancellationToken ct)
    {
        if (_coreWebView2 == null) return false;

        Log("STEP", $"Sending attachment via CDP: {Path.GetFileName(filePath)} ({fileType})");

        var isMedia = fileType.ToLower() == "image" || fileType.ToLower() == "video";
        var selector = isMedia ? _selectors.MediaInput : _selectors.FileInput;

        // Check if input element is available, if not, open the attach menu
        var inputExists = await CheckSelectorExistsAsync(selector);
        if (!inputExists)
        {
            Log("INFO", "Opening attachment menu...");
            var jsMenu = $@"
                (function() {{
                    var attachBtn = document.querySelector(""{_selectors.AttachButton.Replace("\"", "\\\"")}"");
                    if (attachBtn) {{
                        attachBtn.click();
                        return true;
                    }}
                    return false;
                }})();";
            await ExecuteScriptSafeAsync(jsMenu);
            await Task.Delay(1000, ct); // Wait for menu to load inputs
        }

        // We use CDP to set files on input elements securely without triggering the OS dialog
        var fileInjected = await SetFileInputPathAsync(selector, filePath);
        if (!fileInjected)
        {
            Log("ERROR", "Failed to inject file via Chrome DevTools Protocol.");
            return false;
        }

        // Wait for media preview page to load
        Log("INFO", "Waiting for media preview...");
        var previewLoaded = false;
        var start = DateTime.Now;
        while (DateTime.Now - start < TimeSpan.FromSeconds(15))
        {
            ct.ThrowIfCancellationRequested();
            var exists = await CheckSelectorExistsAsync(_selectors.MediaPreviewSendButton);
            if (exists)
            {
                previewLoaded = true;
                break;
            }
            await Task.Delay(500, ct);
        }

        if (!previewLoaded)
        {
            Log("ERROR", "Media preview dialog did not load.");
            return false;
        }

        // Write Caption if provided
        var captionText = captionOverride ?? caption;
        if (!string.IsNullOrEmpty(captionText))
        {
            Log("INFO", "Writing caption...");
            var captionJson = JsonSerializer.Serialize(captionText);
            var captionBoxSel = JsonSerializer.Serialize(_selectors.CaptionBox);
            var jsCaption = $@"
                (function() {{
                    const input = document.querySelector({captionBoxSel});
                    if (!input) return false;
                    input.focus();
                    document.execCommand('selectAll', false, null);
                    document.execCommand('delete', false, null);

                    const text = {captionJson};
                    const lines = text.split('\n');
                    for (let i = 0; i < lines.length; i++) {{
                        if (i > 0) document.execCommand('insertLineBreak');
                        if (lines[i].length) document.execCommand('insertText', false, lines[i]);
                    }}
                    return true;
                }})();";
            await ExecuteScriptSafeAsync(jsCaption);
            await Task.Delay(500, ct);
        }

        // Click Send on preview dialog
        Log("INFO", "Clicking media send button...");
        var jsSend = $@"
            (function() {{
                var sendBtn = document.querySelector(""{_selectors.MediaPreviewSendButton.Replace("\"", "\\\"")}"");
                if (sendBtn) {{
                    sendBtn.click();
                    return true;
                }}
                return false;
            }})();";

        var sendClicked = await ExecuteScriptSafeAsync(jsSend);
        if (sendClicked == "true")
        {
            // Wait for preview to disappear
            start = DateTime.Now;
            while (DateTime.Now - start < TimeSpan.FromSeconds(10))
            {
                var exists = await CheckSelectorExistsAsync(_selectors.MediaPreviewSendButton);
                if (!exists)
                {
                    Log("INFO", "Media message sent successfully.");
                    return true;
                }
                await Task.Delay(500, ct);
            }
        }

        Log("ERROR", "Failed to send media message.");
        return false;
    }

    private async Task<bool> SetFileInputPathAsync(string selector, string filePath)
    {
        if (_coreWebView2 == null) return false;

        try
        {
            // 1. Get the DOM document root
            var docResult = await CallDevToolsProtocolMethodSafeAsync("DOM.getDocument", "{}");
            using var doc = JsonDocument.Parse(docResult);
            var rootNodeId = doc.RootElement.GetProperty("root").GetProperty("nodeId").GetInt32();

            // 2. Query selector to find the input element's nodeId
            var queryParams = JsonSerializer.Serialize(new { nodeId = rootNodeId, selector = selector });
            var queryResult = await CallDevToolsProtocolMethodSafeAsync("DOM.querySelector", queryParams);
            using var query = JsonDocument.Parse(queryResult);
            var nodeId = query.RootElement.GetProperty("nodeId").GetInt32();

            if (nodeId == 0)
            {
                Log("ERROR", $"Element not found for selector: {selector}");
                return false;
            }

            // 3. Set the file input files
            var setFilesParams = JsonSerializer.Serialize(new 
            { 
                nodeId = nodeId, 
                files = new[] { Path.GetFullPath(filePath) } 
            });
            await CallDevToolsProtocolMethodSafeAsync("DOM.setFileInputFiles", setFilesParams);

            // 4. Dispatch change event to the input element so React processes it
            var dispatchJs = $@"
                (function() {{
                    var input = document.querySelector(""{selector.Replace("\"", "\\\"")}"");
                    if (input) {{
                        var event = document.createEvent('HTMLEvents');
                        event.initEvent('change', true, true);
                        input.dispatchEvent(event);
                        return true;
                    }}
                    return false;
                }})();";
            await ExecuteScriptSafeAsync(dispatchJs);

            Log("INFO", $"Successfully set file input '{selector}' to path '{filePath}' using CDP.");
            return true;
        }
        catch (Exception ex)
        {
            Log("ERROR", $"Failed to set file input via CDP: {ex.Message}");
            return false;
        }
    }

    private async Task<bool> CheckSelectorExistsAsync(string selector)
    {
        if (_coreWebView2 == null) return false;
        try
        {
            var js = $"!!document.querySelector(\"{selector.Replace("\"", "\\\"")}\")";
            var result = await ExecuteScriptSafeAsync(js);
            return result == "true";
        }
        catch
        {
            return false;
        }
    }

    private async Task<bool> CheckIsInvalidNumberAsync()
    {
        if (_coreWebView2 == null) return false;

        try
        {
            var markersArrayJson = JsonSerializer.Serialize(_selectors.InvalidNumberMarkers);
            var js = $@"
                (function() {{
                    var markers = {markersArrayJson};
                    
                    // Look for modal/dialog container (WhatsApp Web uses data-animate-modal-popup or role='dialog' for alerts)
                    var modal = document.querySelector(""div[data-animate-modal-popup='true'], div[role='dialog']"");
                    if (!modal) {{
                        return false; // No alert modal, so number is not flagged as invalid
                    }}
                    
                    var targetText = modal.innerText || modal.textContent || '';
                    for (var i = 0; i < markers.length; i++) {{
                        if (targetText.indexOf(markers[i]) >= 0) {{
                            return true;
                        }}
                    }}
                    return false;
                }})();";
            var result = await ExecuteScriptSafeAsync(js);
            return result == "true";
        }
        catch
        {
            return false;
        }
    }

    private async Task DismissInvalidNumberModalAsync()
    {
        if (_coreWebView2 == null) return;
        try
        {
            Log("INFO", "Dismissing invalid number modal...");
            var js = $@"
                (function() {{
                    var okButtonSelector = ""{_selectors.InvalidNumberOkButton.Replace("\"", "\\\"")}"";
                    var buttons = document.querySelectorAll(okButtonSelector);
                    for (var i = 0; i < buttons.length; i++) {{
                        var text = (buttons[i].innerText || buttons[i].textContent || '').trim();
                        if (text === 'موافق' || text === 'OK' || text === 'ok') {{
                            buttons[i].click();
                            return true;
                        }}
                    }}
                    
                    var escEvent = new KeyboardEvent('keydown', {{
                        bubbles: true, cancelable: true, keyCode: 27, key: 'Escape'
                    }});
                    document.dispatchEvent(escEvent);
                    return false;
                }})();";
            await ExecuteScriptSafeAsync(js);
            await Task.Delay(500);
        }
        catch (Exception ex)
        {
            Log("DEBUG", $"Error dismissing invalid number modal: {ex.Message}");
        }
    }

    public void Close()
    {
        _coreWebView2 = null;
        Log("INFO", "WhatsApp Automation Service closed.");
    }
}
