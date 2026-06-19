using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using WhatsAppSender.Core.Automation;
using WhatsAppSender.Core.Data;
using WhatsAppSender.Core.Models;
using WhatsAppSender.Core.Services;

namespace WhatsAppSender.App.ViewModels;

public class ContactSendingRow
{
    public string Name { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string Var1 { get; set; } = string.Empty;
    public string Status { get; set; } = "Pending"; // Pending, Sending, Success, Failed, Invalid
}

public class AttachmentRow
{
    public string FileName { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Caption { get; set; } = string.Empty;
}

public partial class MessageTabItem : ObservableObject
{
    [ObservableProperty]
    private string _header = string.Empty;

    [ObservableProperty]
    private string _text = string.Empty;
}

public partial class MainTabViewModel : ObservableObject
{
    private readonly ContactsRepository _contactsRepo;
    private readonly CampaignsRepository _campaignsRepo;
    private readonly IWhatsAppService _waService;
    private readonly CampaignRunner _runner;
    private readonly SpintaxEngine _spintaxEngine;
    private CancellationTokenSource? _cts;

    [ObservableProperty]
    private ObservableCollection<ContactSendingRow> _contactsList = new();

    [ObservableProperty]
    private ContactSendingRow? _selectedContact;

    [ObservableProperty]
    private ObservableCollection<string> _savedGroups = new();

    [ObservableProperty]
    private string? _selectedGroup;

    [ObservableProperty]
    private string _sourceMode = "File/Manual"; // File/Manual vs Saved Group

    [ObservableProperty]
    private ObservableCollection<MessageTabItem> _messageTabs = new();

    [ObservableProperty]
    private MessageTabItem? _selectedMessageTab;

    [ObservableProperty]
    private bool _sendTextWithImage = false;

    [ObservableProperty]
    private bool _enableSpintax = true;

    [ObservableProperty]
    private string _attachmentPath = string.Empty;

    [ObservableProperty]
    private int _minDelay = 15;

    [ObservableProperty]
    private int _maxDelay = 30;

    [ObservableProperty]
    private bool _isSending = false;

    [ObservableProperty]
    private int _sentCount = 0;

    [ObservableProperty]
    private int _failedCount = 0;

    [ObservableProperty]
    private int _invalidCount = 0;

    [ObservableProperty]
    private int _totalCount = 0;

    [ObservableProperty]
    private int _contactsCount = 0;

    [ObservableProperty]
    private int _groupsCount = 0;

    [ObservableProperty]
    private ObservableCollection<AttachmentRow> _attachmentsList = new();

    [ObservableProperty]
    private double _progressBarValue = 0;

    [ObservableProperty]
    private string _statusMessage = "جاهز / Ready";

    public MainTabViewModel(
        ContactsRepository contactsRepo,
        CampaignsRepository campaignsRepo,
        IWhatsAppService waService,
        CampaignRunner runner,
        SpintaxEngine spintaxEngine)
    {
        _contactsRepo = contactsRepo;
        _campaignsRepo = campaignsRepo;
        _waService = waService;
        _runner = runner;
        _spintaxEngine = spintaxEngine;

        LoadSavedGroups();

        _messageTabs.Add(new MessageTabItem { Header = "Message 1", Text = string.Empty });
        _selectedMessageTab = _messageTabs[0];
    }

    public void LoadSavedGroups()
    {
        var names = _contactsRepo.GetNames();
        SavedGroups = new ObservableCollection<string>(names);
    }

    partial void OnSelectedGroupChanged(string? value)
    {
        if (SourceMode == "Saved Group" && !string.IsNullOrEmpty(value))
        {
            var group = _contactsRepo.GetByName(value);
            if (group != null && group.Contacts != null)
            {
                ContactsList.Clear();
                foreach (var c in group.Contacts)
                {
                    ContactsList.Add(new ContactSendingRow
                    {
                        Name = c.Name,
                        Phone = c.Phone,
                        Status = "Pending"
                    });
                }
                UpdateCounters();
            }
        }
    }

    [RelayCommand]
    private void ImportCSV()
    {
        var dialog = new OpenFileDialog
        {
            Filter = "CSV Files (*.csv)|*.csv|All Files (*.*)|*.*",
            Title = "استيراد جهات الاتصال / Import Contacts"
        };

        if (dialog.ShowDialog() == true)
        {
            try
            {
                var lines = File.ReadAllLines(dialog.FileName);
                if (lines.Length > 0)
                {
                    ContactsList.Clear();
                    // Assumes simple format: Name,Phone or Phone only
                    for (int i = 0; i < lines.Length; i++)
                    {
                        var parts = lines[i].Split(',');
                        if (parts.Length > 0 && !string.IsNullOrWhiteSpace(parts[0]))
                        {
                            var phone = parts.Length > 1 ? parts[1].Trim() : parts[0].Trim();
                            var name = parts.Length > 1 ? parts[0].Trim() : "Contact";
                            
                            // Simple header skip
                            if (phone.ToLower() == "phone" || phone.ToLower() == "number")
                            {
                                continue;
                            }

                            ContactsList.Add(new ContactSendingRow
                            {
                                Name = name,
                                Phone = phone,
                                Status = "Pending"
                            });
                        }
                    }
                    UpdateCounters();
                    StatusMessage = $"تم استيراد {ContactsList.Count} جهات اتصال / Imported {ContactsList.Count} contacts";
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"فشل الاستيراد: {ex.Message}", "خطأ / Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    [RelayCommand]
    private void AddManual()
    {
        // For simplicity, add a placeholder and let user edit, or show simple input prompt
        ContactsList.Add(new ContactSendingRow
        {
            Name = "عميل جديد",
            Phone = "201XXXXXXXXX",
            Status = "Pending"
        });
        UpdateCounters();
    }

    [RelayCommand]
    private void RemoveSelected()
    {
        if (SelectedContact != null)
        {
            ContactsList.Remove(SelectedContact);
            UpdateCounters();
        }
    }

    [RelayCommand]
    private void ClearList()
    {
        ContactsList.Clear();
        UpdateCounters();
    }

    [RelayCommand]
    private void BrowseAttachment()
    {
        var dialog = new OpenFileDialog
        {
            Filter = "All Files (*.*)|*.*",
            Title = "اختر مرفق / Select Attachment"
        };
        if (dialog.ShowDialog() == true)
        {
            AttachmentPath = dialog.FileName;
        }
    }

    [RelayCommand]
    private void TestSpintax()
    {
        if (SelectedMessageTab == null || string.IsNullOrEmpty(SelectedMessageTab.Text)) return;
        var parsed = _spintaxEngine.Parse(SelectedMessageTab.Text);
        MessageBox.Show(parsed, "معاينة النص الدوار / Spintax Preview", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    [RelayCommand]
    private void AddMessageTab()
    {
        var count = MessageTabs.Count + 1;
        var newTab = new MessageTabItem { Header = $"Message {count}", Text = string.Empty };
        MessageTabs.Add(newTab);
        SelectedMessageTab = newTab;
    }

    [RelayCommand]
    private void RemoveMessageTab()
    {
        if (MessageTabs.Count > 1 && SelectedMessageTab != null)
        {
            var index = MessageTabs.IndexOf(SelectedMessageTab);
            MessageTabs.Remove(SelectedMessageTab);
            for (int i = 0; i < MessageTabs.Count; i++)
            {
                MessageTabs[i].Header = $"Message {i + 1}";
            }
            SelectedMessageTab = MessageTabs[Math.Min(index, MessageTabs.Count - 1)];
        }
    }

    public void UpdateCounters()
    {
        TotalCount = ContactsList.Count;
        ContactsCount = ContactsList.Count;
        GroupsCount = SourceMode == "Saved Group" ? 1 : 0;
        SentCount = ContactsList.Count(c => c.Status == "Sent" || c.Status == "Success");
        FailedCount = ContactsList.Count(c => c.Status == "Failed");
        InvalidCount = ContactsList.Count(c => c.Status == "Invalid");
        ProgressBarValue = TotalCount > 0 ? (double)(SentCount + FailedCount + InvalidCount) / TotalCount * 100.0 : 0;
    }

    partial void OnAttachmentPathChanged(string value)
    {
        AttachmentsList.Clear();
        if (!string.IsNullOrEmpty(value))
        {
            var ext = Path.GetExtension(value).ToLower();
            string type = "Document";
            if (ext == ".jpg" || ext == ".png" || ext == ".webp" || ext == ".jpeg") type = "Image";
            else if (ext == ".mp4" || ext == ".avi" || ext == ".mov") type = "Video";

            AttachmentsList.Add(new AttachmentRow
            {
                FileName = Path.GetFileName(value),
                Type = type,
                Caption = string.Empty
            });
        }
    }

    [RelayCommand]
    private async Task StartCampaign()
    {
        if (ContactsList.Count == 0)
        {
            MessageBox.Show("من فضلك أضف جهات اتصال أولاً / Please add contacts first.", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (IsSending) return;

        IsSending = true;
        _cts = new CancellationTokenSource();
        StatusMessage = "جاري الإرسال... / Sending...";

        // Reset status to Pending for all rows
        foreach (var c in ContactsList)
        {
            c.Status = "Pending";
        }
        UpdateCounters();

        var campaign = new Campaign
        {
            Name = string.IsNullOrEmpty(SelectedGroup) ? "حملة مخصصة" : SelectedGroup,
            CsvPath = string.Empty
        };

        var contactsToRun = ContactsList.Select(c => new Contact
        {
            Name = c.Name,
            Phone = c.Phone
        }).ToList();

        string attType = "document";
        if (!string.IsNullOrEmpty(AttachmentPath))
        {
            var ext = Path.GetExtension(AttachmentPath).ToLower();
            if (ext == ".jpg" || ext == ".png" || ext == ".webp" || ext == ".jpeg") attType = "image";
            else if (ext == ".mp4" || ext == ".avi" || ext == ".mov") attType = "video";
        }

        // Setup progress updates from runner
        _runner.OnProgress += (sent, tot) =>
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                UpdateCounters();
            });
        };

        _runner.OnMessageSent += (res) =>
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                var row = ContactsList.FirstOrDefault(c => c.Phone == res.Phone);
                if (row != null)
                {
                    row.Status = res.Status;
                }
                UpdateCounters();
            });
        };

        _runner.OnStatusChanged += (status) =>
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                StatusMessage = status switch
                {
                    "Running" => "جاري الإرسال... / Sending...",
                    "Completed" => "اكتمل الإرسال / Completed",
                    "Stopped" => "تم الإيقاف مؤقتاً / Paused",
                    _ => status
                };
            });
        };

        var messageList = MessageTabs.Select(t => t.Text).Where(txt => !string.IsNullOrWhiteSpace(txt)).ToList();
        if (messageList.Count == 0)
        {
            MessageBox.Show("الرجاء كتابة نص رسالة واحدة على الأقل / Please write at least one message template.", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            IsSending = false;
            return;
        }

        try
        {
            await _runner.RunCampaignAsync(
                campaign,
                contactsToRun,
                messageList,
                string.IsNullOrEmpty(AttachmentPath) ? null : AttachmentPath,
                attType,
                null,
                SendTextWithImage,
                EnableSpintax,
                MinDelay,
                MaxDelay,
                _cts.Token);
        }
        catch (Exception ex)
        {
            StatusMessage = $"فشل الحملة: {ex.Message}";
        }
        finally
        {
            IsSending = false;
            UpdateCounters();
        }
    }

    [RelayCommand]
    private void StopCampaign()
    {
        _cts?.Cancel();
        IsSending = false;
        StatusMessage = "تم إيقاف الإرسال / Sending Stopped";
    }
}
