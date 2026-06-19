using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using WhatsAppSender.Core.Data;
using WhatsAppSender.Core.Models;
using WhatsAppSender.Core.Services;
using WhatsAppSender.Core.Automation;

namespace WhatsAppSender.App.ViewModels;

// 1. CAMPAIGNS (HISTORY LOG) VIEW MODEL
public partial class CampaignsTabViewModel : ObservableObject
{
    private readonly CampaignsRepository _repo;

    [ObservableProperty]
    private ObservableCollection<Campaign> _campaignsList = new();

    [ObservableProperty]
    private Campaign? _selectedCampaign;

    [ObservableProperty]
    private int _totalCampaigns;

    [ObservableProperty]
    private int _totalSent;

    [ObservableProperty]
    private int _totalFailed;

    [ObservableProperty]
    private string _successRatePercent = "0%";

    public CampaignsTabViewModel(CampaignsRepository repo)
    {
        _repo = repo;
        LoadCampaigns();
    }

    [RelayCommand]
    public void LoadCampaigns()
    {
        var dispatcher = Application.Current?.Dispatcher;
        if (dispatcher == null || dispatcher.CheckAccess())
        {
            var list = _repo.GetAll();
            CampaignsList = new ObservableCollection<Campaign>(list);

            TotalCampaigns = list.Count;
            TotalSent = list.Sum(c => c.Sent);
            TotalFailed = list.Sum(c => c.Failed);

            int total = TotalSent + TotalFailed;
            double rate = total > 0 ? (double)TotalSent / total * 100.0 : 0.0;
            SuccessRatePercent = $"{rate:F0}%";
        }
        else
        {
            dispatcher.Invoke(() =>
            {
                var list = _repo.GetAll();
                CampaignsList = new ObservableCollection<Campaign>(list);

                TotalCampaigns = list.Count;
                TotalSent = list.Sum(c => c.Sent);
                TotalFailed = list.Sum(c => c.Failed);

                int total = TotalSent + TotalFailed;
                double rate = total > 0 ? (double)TotalSent / total * 100.0 : 0.0;
                SuccessRatePercent = $"{rate:F0}%";
            });
        }
    }

    [RelayCommand]
    private void DeleteCampaign()
    {
        if (SelectedCampaign == null) return;

        var result = MessageBox.Show(
            $"هل أنت متأكد من حذف الحملة رقم {SelectedCampaign.Id}؟", 
            "تأكيد الحذف", 
            MessageBoxButton.YesNo, 
            MessageBoxImage.Question);

        if (result == MessageBoxResult.Yes)
        {
            _repo.DeleteCampaign(SelectedCampaign.Id);
            LoadCampaigns();
        }
    }
}

// 2. CONTACTS & GROUPS VIEW MODEL
public partial class ContactsTabViewModel : ObservableObject
{
    private readonly ContactsRepository _repo;

    [ObservableProperty]
    private ObservableCollection<ContactGroup> _groupsList = new();

    [ObservableProperty]
    private ContactGroup? _selectedGroup;

    [ObservableProperty]
    private string _newGroupName = string.Empty;

    [ObservableProperty]
    private string _newContactName = string.Empty;

    [ObservableProperty]
    private string _newContactPhone = string.Empty;

    public ContactsTabViewModel(ContactsRepository repo)
    {
        _repo = repo;
        LoadGroups();
    }

    [RelayCommand]
    public void LoadGroups()
    {
        var list = _repo.GetAll();
        GroupsList = new ObservableCollection<ContactGroup>(list);
        if (SelectedGroup != null)
        {
            SelectedGroup = GroupsList.FirstOrDefault(g => g.Id == SelectedGroup.Id);
        }
    }

    [RelayCommand]
    private void AddGroup()
    {
        if (string.IsNullOrWhiteSpace(NewGroupName)) return;
        
        bool success = _repo.CreateGroup(NewGroupName.Trim());
        if (success)
        {
            NewGroupName = string.Empty;
            LoadGroups();
        }
        else
        {
            MessageBox.Show("اسم المجموعة موجود بالفعل", "خطأ", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    [RelayCommand]
    private void DeleteGroup()
    {
        if (SelectedGroup == null) return;
        
        _repo.DeleteGroup(SelectedGroup.Name);
        SelectedGroup = null;
        LoadGroups();
    }

    [RelayCommand]
    private void AddContact()
    {
        if (SelectedGroup == null || string.IsNullOrWhiteSpace(NewContactPhone)) return;

        bool success = _repo.AddContact(SelectedGroup.Name, NewContactPhone.Trim(), NewContactName.Trim());
        if (success)
        {
            NewContactName = string.Empty;
            NewContactPhone = string.Empty;
            LoadGroups();
        }
    }

    [RelayCommand]
    private void DeleteContact(Contact contact)
    {
        if (SelectedGroup == null || contact == null) return;

        _repo.RemoveContact(SelectedGroup.Name, contact.Phone);
        LoadGroups();
    }
}

// 3. TEMPLATES VIEW MODEL
public partial class TemplatesTabViewModel : ObservableObject
{
    private readonly TemplatesRepository _repo;

    [ObservableProperty]
    private ObservableCollection<Template> _templatesList = new();

    [ObservableProperty]
    private Template? _selectedTemplate;

    [ObservableProperty]
    private string _templateName = string.Empty;

    [ObservableProperty]
    private string _templateBody = string.Empty;

    public TemplatesTabViewModel(TemplatesRepository repo)
    {
        _repo = repo;
        LoadTemplates();
    }

    [RelayCommand]
    public void LoadTemplates()
    {
        var list = _repo.GetAll();
        TemplatesList = new ObservableCollection<Template>(list);
    }

    [RelayCommand]
    private void SaveTemplate()
    {
        if (string.IsNullOrWhiteSpace(TemplateName)) return;

        var temp = new Template
        {
            Name = TemplateName.Trim(),
            Body = TemplateBody.Trim()
        };

        _repo.Add(TemplateName.Trim(), TemplateBody.Trim());
        LoadTemplates();
        
        TemplateName = string.Empty;
        TemplateBody = string.Empty;
    }

    [RelayCommand]
    private void LoadSelectedTemplate()
    {
        if (SelectedTemplate == null) return;
        TemplateName = SelectedTemplate.Name;
        TemplateBody = SelectedTemplate.Body;
    }

    [RelayCommand]
    private void DeleteTemplate()
    {
        if (SelectedTemplate == null) return;
        _repo.Delete(SelectedTemplate.Name);
        LoadTemplates();
        TemplateName = string.Empty;
        TemplateBody = string.Empty;
    }
}

// 4. AUTO REPLY VIEW MODEL
public class AutoReplyRule
{
    public string RuleName { get; set; } = string.Empty;
    public string Keywords { get; set; } = string.Empty;
    public string Reply { get; set; } = string.Empty;
    public bool Enabled { get; set; } = true;
}

public partial class AutoReplyTabViewModel : ObservableObject
{
    [ObservableProperty]
    private bool _autoReplyEnabled = true;

    [ObservableProperty]
    private ObservableCollection<AutoReplyRule> _rulesList = new();

    [ObservableProperty]
    private AutoReplyRule? _selectedRule;

    [ObservableProperty]
    private string _ruleName = string.Empty;

    [ObservableProperty]
    private string _ruleKeywords = string.Empty;

    [ObservableProperty]
    private string _ruleReply = string.Empty;

    public AutoReplyTabViewModel()
    {
        LoadRules();
    }

    private void LoadRules()
    {
        // Simple in-memory fallback mimicking python local json file loading
        RulesList = new ObservableCollection<AutoReplyRule>
        {
            new() { RuleName = "ترحيب", Keywords = "مرحبا, سلام, هلا", Reply = "أهلاً بك! كيف يمكنني مساعدتك اليوم؟", Enabled = true },
            new() { RuleName = "الأسعار", Keywords = "سعر, اسعار, بكم", Reply = "أسعار باقاتنا تبدأ من 20 دولار شهرياً.", Enabled = true }
        };
    }

    [RelayCommand]
    private void AddRule()
    {
        if (string.IsNullOrWhiteSpace(RuleName) || string.IsNullOrWhiteSpace(RuleKeywords) || string.IsNullOrWhiteSpace(RuleReply)) return;

        RulesList.Add(new AutoReplyRule
        {
            RuleName = RuleName.Trim(),
            Keywords = RuleKeywords.Trim(),
            Reply = RuleReply.Trim(),
            Enabled = true
        });

        RuleName = string.Empty;
        RuleKeywords = string.Empty;
        RuleReply = string.Empty;
    }

    [RelayCommand]
    private void DeleteRule()
    {
        if (SelectedRule == null) return;
        RulesList.Remove(SelectedRule);
    }

    [RelayCommand]
    private void ToggleRule()
    {
        if (SelectedRule == null) return;
        SelectedRule.Enabled = !SelectedRule.Enabled;
        // Trigger list refresh
        var temp = RulesList;
        RulesList = new ObservableCollection<AutoReplyRule>(temp);
    }
}

// 5. INCOMING MESSAGES (INBOX) VIEW MODEL
public class ReceivedMessage
{
    public string Date { get; set; } = string.Empty;
    public string Sender { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
}

public partial class ReceivedTabViewModel : ObservableObject
{
    [ObservableProperty]
    private ObservableCollection<ReceivedMessage> _messagesList = new();

    [ObservableProperty]
    private string _searchQuery = string.Empty;

    public ReceivedTabViewModel()
    {
        // Empty by default, populated dynamically at runtime
    }

    public void AddMessage(string sender, string message)
    {
        Application.Current.Dispatcher.Invoke(() =>
        {
            MessagesList.Add(new ReceivedMessage
            {
                Date = DateTime.Now.ToString("yyyy-MM-dd HH:mm"),
                Sender = sender,
                Message = message
            });
        });
    }

    [RelayCommand]
    private void ClearAll()
    {
        MessagesList.Clear();
    }
}

// 6. SCHEDULER VIEW MODEL
public partial class SchedulerTabViewModel : ObservableObject
{
    private readonly ScheduledCampaignsRepository _repo;

    [ObservableProperty]
    private ObservableCollection<ScheduledCampaign> _scheduledCampaigns = new();

    [ObservableProperty]
    private ScheduledCampaign? _selectedCampaign;

    public SchedulerTabViewModel(ScheduledCampaignsRepository repo)
    {
        _repo = repo;
        LoadScheduled();
    }

    [RelayCommand]
    public void LoadScheduled()
    {
        var dispatcher = Application.Current?.Dispatcher;
        if (dispatcher == null || dispatcher.CheckAccess())
        {
            ScheduledCampaigns = new ObservableCollection<ScheduledCampaign>(_repo.GetAll());
        }
        else
        {
            dispatcher.Invoke(() =>
            {
                ScheduledCampaigns = new ObservableCollection<ScheduledCampaign>(_repo.GetAll());
            });
        }
    }

    [RelayCommand]
    private void CancelCampaign()
    {
        if (SelectedCampaign == null) return;
        _repo.UpdateStatus(SelectedCampaign.Id, "cancelled");
        LoadScheduled();
    }

    [RelayCommand]
    private void DeleteCampaign()
    {
        if (SelectedCampaign == null) return;
        _repo.Delete(SelectedCampaign.Id);
        LoadScheduled();
    }
}

// 7. SYSTEM LOGS VIEW MODEL
public class LogItem
{
    public string Time { get; set; } = string.Empty;
    public string Level { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
}

public partial class LogsTabViewModel : ObservableObject
{
    [ObservableProperty]
    private ObservableCollection<LogItem> _logsList = new();

    public void AddLog(string level, string message)
    {
        Application.Current.Dispatcher.Invoke(() =>
        {
            LogsList.Insert(0, new LogItem
            {
                Time = DateTime.Now.ToString("HH:mm:ss"),
                Level = level,
                Message = message
            });
        });
    }

    [RelayCommand]
    private void ClearLogs()
    {
        LogsList.Clear();
    }
}

// 8. GOOGLE MAPS SCRAPER VIEW MODEL
public class ScrapedBusiness
{
    public string Name { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
}

public partial class GMapsTabViewModel : ObservableObject
{
    private Microsoft.Web.WebView2.Wpf.WebView2? _webView;
    private System.Windows.Threading.DispatcherTimer? _timer;
    private int _limit = 50;

    [ObservableProperty]
    private string _searchQuery = string.Empty;

    [ObservableProperty]
    private int _limitValue = 50;

    [ObservableProperty]
    private bool _isScrapingRunning;

    [ObservableProperty]
    private int _scrapedCount;

    [ObservableProperty]
    private ObservableCollection<ScrapedBusiness> _scrapedList = new();

    [ObservableProperty]
    private ScrapedBusiness? _selectedBusiness;

    public void SetWebView(Microsoft.Web.WebView2.Wpf.WebView2 webView)
    {
        _webView = webView;
    }

    [RelayCommand]
    private void StartScraping()
    {
        if (string.IsNullOrWhiteSpace(SearchQuery))
        {
            MessageBox.Show("يرجى إدخال كلمة البحث أولاً", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (_webView == null || _webView.CoreWebView2 == null)
        {
            MessageBox.Show("لم يتم تهيئة المتصفح بعد", "خطأ", MessageBoxButton.OK, MessageBoxImage.Error);
            return;
        }

        ScrapedList.Clear();
        ScrapedCount = 0;
        IsScrapingRunning = true;
        _limit = LimitValue;

        // Navigate to search
        string encodedQuery = Uri.EscapeDataString(SearchQuery);
        _webView.Source = new Uri($"https://www.google.com/maps/search/{encodedQuery}");

        // Start polling timer for scrolling and scraping
        _timer = new System.Windows.Threading.DispatcherTimer();
        _timer.Interval = TimeSpan.FromSeconds(3);
        _timer.Tick += async (s, e) =>
        {
            if (!IsScrapingRunning) return;

            if (ScrapedList.Count >= _limit)
            {
                StopScraping();
                MessageBox.Show("تم الوصول إلى الحد الأقصى المطلوب للنتائج", "اكتمل البحث", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            // JavaScript to scroll and scrape
            string js = @"
                (function() {
                    let feed = document.querySelector('div[role=""feed""]');
                    if (feed) {
                        feed.scrollTop = feed.scrollHeight;
                    }
                    
                    let items = document.querySelectorAll('a[href*=""/maps/place/""]');
                    let results = [];
                    for (let item of items) {
                        try {
                            let parent = item.parentElement;
                            if (!parent) continue;
                            let text = parent.innerText || '';
                            let lines = text.split('\n');
                            let name = lines[0] || 'Unknown';
                            
                            // Regex for phone number
                            let phoneMatch = text.match(/(\+?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{3,4}[\s-]?\d{3,4})/);
                            if (phoneMatch) {
                                let phone = phoneMatch[0].replace(/[^\d+]/g, '');
                                if (phone.replace('+', '').length >= 7) {
                                    results.push({ name: name, phone: phone });
                                }
                            }
                        } catch (e) {}
                    }
                    return JSON.stringify(results);
                })()";

            try
            {
                string jsonResult = await _webView.CoreWebView2.ExecuteScriptAsync(js);
                if (!string.IsNullOrEmpty(jsonResult) && jsonResult != "null")
                {
                    string unescaped = System.Text.Json.Nodes.JsonNode.Parse(jsonResult)?.GetValue<string>() ?? "[]";
                    var list = System.Text.Json.JsonSerializer.Deserialize<List<ScrapedBusiness>>(unescaped);
                    if (list != null)
                    {
                        foreach (var biz in list)
                        {
                            if (ScrapedList.Count >= _limit) break;

                            if (!ScrapedList.Any(b => b.Phone == biz.Phone))
                            {
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    ScrapedList.Add(biz);
                                    ScrapedCount = ScrapedList.Count;
                                });
                            }
                        }
                    }
                }
            }
            catch { }
        };
        _timer.Start();
    }

    [RelayCommand]
    private void StopScraping()
    {
        if (_timer != null)
        {
            _timer.Stop();
            _timer = null;
        }
        IsScrapingRunning = false;
    }

    [RelayCommand]
    private void ImportToCampaign()
    {
        if (ScrapedList.Count == 0)
        {
            MessageBox.Show("لا توجد أرقام مستخرجة لاستيرادها", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        // Find main window and main view model dynamically
        var mainVM = Application.Current.MainWindow?.DataContext as MainWindowViewModel;
        if (mainVM != null)
        {
            int count = 0;
            foreach (var biz in ScrapedList)
            {
                if (!mainVM.MainTab.ContactsList.Any(c => c.Phone == biz.Phone))
                {
                    mainVM.MainTab.ContactsList.Add(new ContactSendingRow
                    {
                        Name = biz.Name,
                        Phone = biz.Phone,
                        Status = "Pending"
                    });
                    count++;
                }
            }
            mainVM.MainTab.UpdateCounters();
            MessageBox.Show($"تم استيراد {count} جهات اتصال بنجاح إلى القائمة الرئيسية!", "تم", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    [RelayCommand]
    private void ExportScraped()
    {
        if (ScrapedList.Count == 0)
        {
            MessageBox.Show("لا توجد بيانات لتصديرها", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        var saveFileDialog = new SaveFileDialog
        {
            Filter = "CSV Files (*.csv)|*.csv",
            DefaultExt = ".csv",
            FileName = $"gmaps_{DateTime.Now:yyyyMMdd_HHmmss}.csv"
        };
        if (saveFileDialog.ShowDialog() == true)
        {
            try
            {
                var lines = new List<string> { "Name,Phone" };
                lines.AddRange(ScrapedList.Select(b => $"\"{b.Name.Replace("\"", "\"\"")}\",{b.Phone}"));
                File.WriteAllLines(saveFileDialog.FileName, lines);
                MessageBox.Show($"تم تصدير {ScrapedList.Count} جهات اتصال بنجاح!", "تم", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"خطأ في التصدير: {ex.Message}", "خطأ", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    public void ReceiveScrapedData(string json)
    {
        try
        {
            var biz = System.Text.Json.JsonSerializer.Deserialize<ScrapedBusiness>(json);
            if (biz != null && !string.IsNullOrEmpty(biz.Phone))
            {
                if (ScrapedList.Count < _limit && !ScrapedList.Any(b => b.Phone == biz.Phone))
                {
                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        ScrapedList.Add(biz);
                        ScrapedCount = ScrapedList.Count;
                    });
                }
            }
        }
        catch { }
    }
}

// 9. ACCOUNT WARMER VIEW MODEL
public partial class WarmerTabViewModel : ObservableObject
{
    private readonly WhatsAppAutomationService _whatsappService;
    private readonly SpintaxEngine _spintax;
    private CancellationTokenSource? _cts;
    private int _sentCount = 0;

    [ObservableProperty]
    private ObservableCollection<string> _friendlyContacts = new();

    [ObservableProperty]
    private ObservableCollection<string> _msgTemplates = new();

    [ObservableProperty]
    private string _newContactPhone = string.Empty;

    [ObservableProperty]
    private string _newMsgTemplate = string.Empty;

    [ObservableProperty]
    private string _selectedContact = string.Empty;

    [ObservableProperty]
    private string _selectedMsg = string.Empty;

    [ObservableProperty]
    private int _intervalMinutes = 30;

    [ObservableProperty]
    private int _dailyLimit = 20;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(IsWarmNotRunning))]
    private bool _isWarmRunning;

    public bool IsWarmNotRunning => !IsWarmRunning;

    [ObservableProperty]
    private int _chatsCount;

    [ObservableProperty]
    private string _warmerLogText = string.Empty;

    public WarmerTabViewModel(WhatsAppAutomationService whatsappService, SpintaxEngine spintax)
    {
        _whatsappService = whatsappService;
        _spintax = spintax;

        // Default templates
        MsgTemplates.Add("السلام عليكم، كيف حالك؟");
        MsgTemplates.Add("مرحبا! شو أخبارك اليوم؟");
        MsgTemplates.Add("{مرحبا|أهلاً|هلا} {كيف حالك|شلونك|إيش أخبارك}؟");
    }

    [RelayCommand]
    private void AddContact()
    {
        if (string.IsNullOrWhiteSpace(NewContactPhone)) return;
        var phone = NewContactPhone.Trim().Replace("+", "");
        if (!FriendlyContacts.Contains(phone))
        {
            FriendlyContacts.Add(phone);
            NewContactPhone = string.Empty;
        }
    }

    [RelayCommand]
    private void DeleteContact()
    {
        if (!string.IsNullOrEmpty(SelectedContact))
        {
            FriendlyContacts.Remove(SelectedContact);
        }
    }

    [RelayCommand]
    private void AddMessage()
    {
        if (string.IsNullOrWhiteSpace(NewMsgTemplate)) return;
        if (!MsgTemplates.Contains(NewMsgTemplate.Trim()))
        {
            MsgTemplates.Add(NewMsgTemplate.Trim());
            NewMsgTemplate = string.Empty;
        }
    }

    [RelayCommand]
    private void DeleteMessage()
    {
        if (!string.IsNullOrEmpty(SelectedMsg))
        {
            MsgTemplates.Remove(SelectedMsg);
        }
    }

    [RelayCommand]
    private async Task StartWarmer()
    {
        if (FriendlyContacts.Count == 0)
        {
            MessageBox.Show("يرجى إضافة جهة اتصال ودية واحدة على الأقل", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (MsgTemplates.Count == 0)
        {
            MessageBox.Show("يرجى إضافة قالب رسالة واحد على الأقل", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        bool loggedIn = await _whatsappService.IsLoggedInAsync();
        if (!loggedIn)
        {
            MessageBox.Show("يرجى تسجيل الدخول إلى واتساب أولاً", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        IsWarmRunning = true;
        _sentCount = 0;
        ChatsCount = 0;
        _cts = new CancellationTokenSource();
        LogWarmer("بدأ تهيئة الحساب (Account Warmer started)");

        var ct = _cts.Token;
        _ = Task.Run(async () =>
        {
            var rand = new Random();
            while (!ct.IsCancellationRequested && _sentCount < DailyLimit)
            {
                string contact = FriendlyContacts[rand.Next(FriendlyContacts.Count)];
                string msgTemplate = MsgTemplates[rand.Next(MsgTemplates.Count)];
                string message = _spintax.Parse(msgTemplate);

                try
                {
                    LogWarmer($"جاري الإرسال إلى {contact}...");
                    await _whatsappService.SendMessageAsync(contact, message, null, null, null, false, ct);
                    _sentCount++;
                    ChatsCount = _sentCount;
                    LogWarmer($"✅ تم الإرسال بنجاح إلى {contact}: \"{message}\"");
                }
                catch (Exception ex)
                {
                    LogWarmer($"❌ فشل الإرسال إلى {contact}: {ex.Message}");
                }

                if (ct.IsCancellationRequested || _sentCount >= DailyLimit) break;

                int sleepMinutes = IntervalMinutes;
                LogWarmer($"الانتظار لمدة {sleepMinutes} دقيقة قبل الرسالة التالية...");
                
                for (int i = 0; i < sleepMinutes * 60; i++)
                {
                    if (ct.IsCancellationRequested) break;
                    await Task.Delay(1000);
                }
            }

            IsWarmRunning = false;
            LogWarmer($"انتهى تشغيل تهيئة الحساب. إجمالي الرسائل المرسلة: {_sentCount}");
        }, ct);
    }

    [RelayCommand]
    private void StopWarmer()
    {
        _cts?.Cancel();
        IsWarmRunning = false;
        LogWarmer("تم إيقاف عملية تهيئة الحساب");
    }

    private void LogWarmer(string msg)
    {
        string timestamp = DateTime.Now.ToString("HH:mm:ss");
        Application.Current.Dispatcher.Invoke(() =>
        {
            WarmerLogText += $"[{timestamp}] {msg}\n";
        });
    }
}

// 10. WORKFLOWS VIEW MODEL
public class WorkflowStep
{
    public int Number { get; set; }
    public string Type { get; set; } = "Message"; // Message, Image, Document, Wait
    public string Content { get; set; } = string.Empty;
    public string Delay { get; set; } = "1h"; // e.g. 5m, 1h, 2d
}

public class WorkflowData
{
    public string Name { get; set; } = string.Empty;
    public List<WorkflowStep> Steps { get; set; } = new();
    public string Created { get; set; } = string.Empty;
    public string Updated { get; set; } = string.Empty;
}

public partial class WorkflowsTabViewModel : ObservableObject
{
    [ObservableProperty]
    private ObservableCollection<WorkflowData> _workflowsList = new();

    [ObservableProperty]
    private WorkflowData? _selectedWorkflow;

    [ObservableProperty]
    private string _workflowName = string.Empty;

    [ObservableProperty]
    private ObservableCollection<WorkflowStep> _stepsList = new();

    [ObservableProperty]
    private WorkflowStep? _selectedStep;

    private readonly string _filePath;

    public WorkflowsTabViewModel()
    {
        _filePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "workflows.json");
        LoadWorkflows();
    }

    public void LoadWorkflows()
    {
        try
        {
            var dir = Path.GetDirectoryName(_filePath);
            if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
            {
                Directory.CreateDirectory(dir);
            }

            if (File.Exists(_filePath))
            {
                var json = File.ReadAllText(_filePath);
                var list = System.Text.Json.JsonSerializer.Deserialize<List<WorkflowData>>(json) ?? new();
                WorkflowsList = new ObservableCollection<WorkflowData>(list);
            }
            else
            {
                WorkflowsList = new ObservableCollection<WorkflowData>();
            }
        }
        catch { }
    }

    private void SaveAllWorkflows()
    {
        try
        {
            var json = System.Text.Json.JsonSerializer.Serialize(WorkflowsList.ToList(), new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(_filePath, json);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"خطأ أثناء حفظ الملف: {ex.Message}", "خطأ", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    [RelayCommand]
    private void NewWorkflow()
    {
        WorkflowName = string.Empty;
        StepsList.Clear();
        SelectedWorkflow = null;
    }

    [RelayCommand]
    private void LoadSelectedWorkflow()
    {
        if (SelectedWorkflow == null) return;
        WorkflowName = SelectedWorkflow.Name;
        StepsList = new ObservableCollection<WorkflowStep>(SelectedWorkflow.Steps);
    }

    [RelayCommand]
    private void SaveWorkflow()
    {
        if (string.IsNullOrWhiteSpace(WorkflowName))
        {
            MessageBox.Show("يرجى إدخال اسم مسار العمل أولاً", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        if (StepsList.Count == 0)
        {
            MessageBox.Show("يرجى إضافة خطوة واحدة على الأقل في مسار العمل", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        var existing = WorkflowsList.FirstOrDefault(w => w.Name.Equals(WorkflowName, StringComparison.OrdinalIgnoreCase));
        if (existing != null)
        {
            existing.Steps = StepsList.ToList();
            existing.Updated = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
        }
        else
        {
            var newWf = new WorkflowData
            {
                Name = WorkflowName.Trim(),
                Steps = StepsList.ToList(),
                Created = DateTime.Now.ToString("yyyy-MM-dd HH:mm"),
                Updated = DateTime.Now.ToString("yyyy-MM-dd HH:mm")
            };
            WorkflowsList.Add(newWf);
        }

        SaveAllWorkflows();
        LoadWorkflows();
        MessageBox.Show($"تم حفظ مسار العمل \"{WorkflowName}\" بنجاح!", "تم الحفظ", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    [RelayCommand]
    private void DeleteWorkflow()
    {
        if (SelectedWorkflow == null) return;
        
        var result = MessageBox.Show($"هل أنت متأكد من حذف مسار العمل \"{SelectedWorkflow.Name}\"؟", "تأكيد الحذف", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (result == MessageBoxResult.Yes)
        {
            WorkflowsList.Remove(SelectedWorkflow);
            SaveAllWorkflows();
            NewWorkflow();
        }
    }

    [RelayCommand]
    private void AddStep()
    {
        int num = StepsList.Count + 1;
        StepsList.Add(new WorkflowStep
        {
            Number = num,
            Type = "Message",
            Content = "نص رسالة خطوة " + num,
            Delay = "1h"
        });
    }

    [RelayCommand]
    private void DeleteStep()
    {
        if (SelectedStep == null) return;
        StepsList.Remove(SelectedStep);
        for (int i = 0; i < StepsList.Count; i++)
        {
            StepsList[i].Number = i + 1;
        }
        var temp = StepsList;
        StepsList = new ObservableCollection<WorkflowStep>(temp);
    }
}

// 11. NUMBERS FILTER VIEW MODEL
public class FilteredNumber
{
    public string Phone { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string CheckTime { get; set; } = string.Empty;
    public string StatusTag { get; set; } = "pending";
}

public partial class NumbersFilterTabViewModel : ObservableObject
{
    private readonly WhatsAppAutomationService _whatsappService;
    private CancellationTokenSource? _filterCts;

    [ObservableProperty]
    private ObservableCollection<FilteredNumber> _numbersList = new();

    [ObservableProperty]
    private FilteredNumber? _selectedNumber;

    [ObservableProperty]
    private int _totalCount;

    [ObservableProperty]
    private int _validCount;

    [ObservableProperty]
    private int _invalidCount;

    [ObservableProperty]
    private int _pendingCount;

    [ObservableProperty]
    private double _progressBarValue;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(IsFilterNotRunning))]
    private bool _isFilterRunning;

    public bool IsFilterNotRunning => !IsFilterRunning;

    public NumbersFilterTabViewModel(WhatsAppAutomationService whatsappService)
    {
        _whatsappService = whatsappService;
    }

    [RelayCommand]
    private void ImportFromCSV()
    {
        var openFileDialog = new OpenFileDialog
        {
            Filter = "CSV Files (*.csv)|*.csv|Text Files (*.txt)|*.txt|All Files (*.*)|*.*",
            Title = "استيراد أرقام للفلترة"
        };
        if (openFileDialog.ShowDialog() == true)
        {
            try
            {
                var lines = File.ReadAllLines(openFileDialog.FileName);
                int count = 0;
                foreach (var line in lines)
                {
                    var phone = line.Trim().Replace("+", "").Replace(" ", "");
                    if (!string.IsNullOrWhiteSpace(phone) && !NumbersList.Any(n => n.Phone == phone))
                    {
                        NumbersList.Add(new FilteredNumber
                        {
                            Phone = phone,
                            Status = "معلق / Pending",
                            CheckTime = "—",
                            StatusTag = "pending"
                        });
                        count++;
                    }
                }
                UpdateStats();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"خطأ في الاستيراد: {ex.Message}", "خطأ", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }

    [RelayCommand]
    private void AddManual()
    {
        var win = new Window
        {
            Title = "إضافة رقم يدوياً",
            Width = 300,
            Height = 150,
            WindowStartupLocation = WindowStartupLocation.CenterOwner,
            Background = System.Windows.Media.Brushes.DimGray,
            Owner = Application.Current.MainWindow
        };
        var sp = new StackPanel { Margin = new Thickness(10) };
        var txt = new TextBox { Height = 34, Margin = new Thickness(0, 0, 0, 10) };
        var btn = new Button { Content = "إضافة / Add", Height = 30 };
        btn.Click += (s, e) =>
        {
            var phone = txt.Text.Trim().Replace("+", "").Replace(" ", "");
            if (!string.IsNullOrWhiteSpace(phone) && !NumbersList.Any(n => n.Phone == phone))
            {
                NumbersList.Add(new FilteredNumber
                {
                    Phone = phone,
                    Status = "معلق / Pending",
                    CheckTime = "—",
                    StatusTag = "pending"
                });
                UpdateStats();
            }
            win.Close();
        };
        sp.Children.Add(txt);
        sp.Children.Add(btn);
        win.Content = sp;
        win.ShowDialog();
    }

    [RelayCommand]
    private void ClearList()
    {
        NumbersList.Clear();
        UpdateStats();
    }

    private void UpdateStats()
    {
        TotalCount = NumbersList.Count;
        ValidCount = NumbersList.Count(n => n.StatusTag == "valid");
        InvalidCount = NumbersList.Count(n => n.StatusTag == "invalid");
        PendingCount = TotalCount - ValidCount - InvalidCount;
        ProgressBarValue = TotalCount > 0 ? (double)(ValidCount + InvalidCount) / TotalCount * 100.0 : 0;
    }

    [RelayCommand]
    private async Task StartFilter()
    {
        var pending = NumbersList.Where(n => n.StatusTag == "pending").ToList();
        if (pending.Count == 0)
        {
            MessageBox.Show("لا توجد أرقام معلقة للتحقق منها", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        bool loggedIn = await _whatsappService.IsLoggedInAsync();
        if (!loggedIn)
        {
            MessageBox.Show("يرجى تسجيل الدخول إلى واتساب أولاً", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        IsFilterRunning = true;
        _filterCts = new CancellationTokenSource();
        var ct = _filterCts.Token;

        try
        {
            var rand = new Random();
            foreach (var item in pending)
            {
                if (ct.IsCancellationRequested) break;

                item.Status = "يجري التحقق... / Checking...";
                
                // Trigger item update notification by removing and re-inserting, or just refresh list
                var index = NumbersList.IndexOf(item);
                if (index >= 0)
                {
                    NumbersList[index] = new FilteredNumber { Phone = item.Phone, Status = item.Status, CheckTime = item.CheckTime, StatusTag = item.StatusTag };
                }

                try
                {
                    bool exists = await _whatsappService.CheckNumberExistsAsync(item.Phone, ct);
                    item.CheckTime = DateTime.Now.ToString("HH:mm:ss");
                    if (exists)
                    {
                        item.Status = "نشط / Active";
                        item.StatusTag = "valid";
                    }
                    else
                    {
                        item.Status = "غير نشط / Non-Active";
                        item.StatusTag = "invalid";
                    }
                }
                catch (Exception)
                {
                    item.Status = "خطأ في التحقق / Error";
                    item.StatusTag = "error";
                }

                if (index >= 0)
                {
                    NumbersList[index] = new FilteredNumber { Phone = item.Phone, Status = item.Status, CheckTime = item.CheckTime, StatusTag = item.StatusTag };
                }

                UpdateStats();

                int delayMs = rand.Next(2000, 5000);
                await Task.Delay(delayMs, ct);
            }
        }
        catch (TaskCanceledException) { }
        finally
        {
            IsFilterRunning = false;
            _filterCts = null;
        }
    }

    [RelayCommand]
    private void StopFilter()
    {
        _filterCts?.Cancel();
        IsFilterRunning = false;
    }

    [RelayCommand]
    private void Export(string type)
    {
        var listToExport = NumbersList.AsEnumerable();
        if (type == "valid") listToExport = listToExport.Where(n => n.StatusTag == "valid");
        else if (type == "invalid") listToExport = listToExport.Where(n => n.StatusTag == "invalid");

        if (!listToExport.Any())
        {
            MessageBox.Show("لا توجد بيانات مطابقة للتصدير", "تنبيه", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        var saveFileDialog = new SaveFileDialog
        {
            Filter = "CSV Files (*.csv)|*.csv",
            DefaultExt = ".csv",
            FileName = $"filtered_{type}_{DateTime.Now:yyyyMMdd_HHmmss}.csv"
        };
        if (saveFileDialog.ShowDialog() == true)
        {
            try
            {
                var lines = new List<string> { "Phone,Status,CheckTime" };
                lines.AddRange(listToExport.Select(n => $"{n.Phone},{n.Status},{n.CheckTime}"));
                File.WriteAllLines(saveFileDialog.FileName, lines);
                MessageBox.Show($"تم تصدير {listToExport.Count()} أرقام بنجاح!", "تم", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"خطأ في التصدير: {ex.Message}", "خطأ", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
