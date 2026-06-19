using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using WhatsAppSender.Core.Data;
using WhatsAppSender.Core.Models;
using WhatsAppSender.Core.Services;

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

// 8. OTHER TAB PLACEHOLDERS (WARMER, WORKFLOWS, GOOGLE MAPS)
public partial class WarmerTabViewModel : ObservableObject
{
    [ObservableProperty] private bool _isWarmRunning;
    [ObservableProperty] private int _chatsCount;
}

public partial class WorkflowsTabViewModel : ObservableObject
{
    [ObservableProperty] private string _workflowName = string.Empty;
}

public partial class GMapsTabViewModel : ObservableObject
{
    [ObservableProperty] private string _searchQuery = string.Empty;
    [ObservableProperty] private bool _isScrapingRunning;
    [ObservableProperty] private int _scrapedCount;
}
