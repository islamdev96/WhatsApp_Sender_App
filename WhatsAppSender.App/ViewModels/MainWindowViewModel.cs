using System;
using System.Collections.Generic;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using WhatsAppSender.Core.Automation;
using WhatsAppSender.Core.Data;
using WhatsAppSender.Core.Services;
using WhatsAppSender.Core.Models;
using System.Threading;

namespace WhatsAppSender.App.ViewModels;

public partial class MainWindowViewModel : ObservableObject
{
    private readonly LicensingService _licensingService;
    
    // Core Services
    public Database DB { get; }
    public ContactsRepository ContactsRepo { get; }
    public CampaignsRepository CampaignsRepo { get; }
    public TemplatesRepository TemplatesRepo { get; }
    public ScheduledCampaignsRepository ScheduledRepo { get; }
    public WhatsAppAutomationService WhatsAppService { get; }
    public SpintaxEngine Spintax { get; }
    public SafetyService Safety { get; }
    public CampaignRunner CampaignRunnerInstance { get; }
    public SchedulerService Scheduler { get; }

    // Tab ViewModels
    public MainTabViewModel MainTab { get; }
    public CampaignsTabViewModel CampaignsTab { get; }
    public ContactsTabViewModel ContactsTab { get; }
    public TemplatesTabViewModel TemplatesTab { get; }
    public SchedulerTabViewModel SchedulerTab { get; }
    public AutoReplyTabViewModel AutoReplyTab { get; }
    public ReceivedTabViewModel ReceivedTab { get; }
    public LogsTabViewModel LogsTab { get; }
    public WarmerTabViewModel WarmerTab { get; }
    public WorkflowsTabViewModel WorkflowsTab { get; }
    public GMapsTabViewModel GMapsTab { get; }

    [ObservableProperty]
    private bool _isActivated;

    [ObservableProperty]
    private string _hwid = string.Empty;

    [ObservableProperty]
    private string _activationKey = string.Empty;

    [ObservableProperty]
    private string _activationError = string.Empty;

    [ObservableProperty]
    private string _currentTabName = "Campaigns";

    [ObservableProperty]
    private string _selectedLanguage = "Ar";

    [ObservableProperty]
    private string _selectedTheme = "Dark";

    [ObservableProperty]
    private bool _isBrowserVisible = true;

    public MainWindowViewModel()
    {
        // 1. Initialize DB & Repos
        DB = new Database();
        ContactsRepo = new ContactsRepository(DB);
        CampaignsRepo = new CampaignsRepository(DB);
        TemplatesRepo = new TemplatesRepository(DB);
        ScheduledRepo = new ScheduledCampaignsRepository(DB);

        // 2. Initialize Licensing & Basic Services
        _licensingService = new LicensingService();
        Hwid = _licensingService.GetHWID();
        CheckActivation();

        Spintax = new SpintaxEngine();
        Safety = new SafetyService();
        WhatsAppService = new WhatsAppAutomationService();

        // Setup diagnostics logger
        LogsTab = new LogsTabViewModel();
        WhatsAppService.OnDiagnosticLog += (level, message, detail) =>
        {
            LogsTab.AddLog(level, $"{message} {(detail != null ? $"({detail})" : "")}");
        };

        // 3. Initialize Campaign Runner & Scheduler
        CampaignRunnerInstance = new CampaignRunner(WhatsAppService, CampaignsRepo, Spintax, Safety);
        Scheduler = new SchedulerService(ScheduledRepo, ContactsRepo);
        
        Scheduler.OnLog += (level, msg) =>
        {
            LogsTab.AddLog(level, $"[Scheduler] {msg}");
        };

        // 4. Initialize Child ViewModels
        MainTab = new MainTabViewModel(ContactsRepo, CampaignsRepo, WhatsAppService, CampaignRunnerInstance, Spintax);
        CampaignsTab = new CampaignsTabViewModel(CampaignsRepo);
        ContactsTab = new ContactsTabViewModel(ContactsRepo);
        TemplatesTab = new TemplatesTabViewModel(TemplatesRepo);
        SchedulerTab = new SchedulerTabViewModel(ScheduledRepo);
        AutoReplyTab = new AutoReplyTabViewModel();
        ReceivedTab = new ReceivedTabViewModel();
        WarmerTab = new WarmerTabViewModel();
        WorkflowsTab = new WorkflowsTabViewModel();
        GMapsTab = new GMapsTabViewModel();

        // Start Scheduler Polling Loop
        Scheduler.Start(async (scheduledCamp, contacts) =>
        {
            // Scheduled Campaign callback
            try
            {
                var camp = new Campaign
                {
                    Name = scheduledCamp.Name,
                    CsvPath = string.Empty
                };

                await CampaignRunnerInstance.RunCampaignAsync(
                    camp,
                    contacts,
                    scheduledCamp.Message,
                    null, // scheduled campaign attachments are json, for simplicity start with text only first
                    null,
                    null,
                    false,
                    true,
                    15,
                    30,
                    CancellationToken.None);

                // Reload campaign stats and logs after a schedule completes
                CampaignsTab.LoadCampaigns();
                return true;
            }
            catch (Exception ex)
            {
                LogsTab.AddLog("ERROR", $"Scheduled campaign run failed: {ex.Message}");
                return false;
            }
        });
    }

    private void CheckActivation()
    {
        IsActivated = _licensingService.VerifyStoredLicense();
    }

    [RelayCommand]
    private void Activate()
    {
        if (string.IsNullOrWhiteSpace(ActivationKey))
        {
            ActivationError = "الرجاء إدخال مفتاح التفعيل / Please enter activation key";
            return;
        }

        bool success = _licensingService.SaveLicenseKey(ActivationKey);
        if (success)
        {
            IsActivated = true;
            ActivationError = string.Empty;
            // Reload Main Tab data on activation success
            MainTab.LoadSavedGroups();
        }
        else
        {
            ActivationError = "مفتاح تفعيل غير صحيح لهذا الجهاز / Invalid key for this device";
        }
    }

    [RelayCommand]
    private void Navigate(string tabName)
    {
        CurrentTabName = tabName;
        
        // Refresh respective tab lists on navigation
        if (tabName == "Campaigns") CampaignsTab.LoadCampaigns();
        else if (tabName == "Contacts") ContactsTab.LoadGroups();
        else if (tabName == "Templates") TemplatesTab.LoadTemplates();
        else if (tabName == "Scheduler") SchedulerTab.LoadScheduled();
        else if (tabName == "Main") MainTab.LoadSavedGroups();
    }

    [RelayCommand]
    private void ToggleLanguage()
    {
        SelectedLanguage = SelectedLanguage == "Ar" ? "En" : "Ar";
        App.ChangeLanguage(SelectedLanguage);
    }

    [RelayCommand]
    private void ToggleTheme()
    {
        SelectedTheme = SelectedTheme == "Dark" ? "Light" : "Dark";
        App.ChangeTheme(SelectedTheme);
    }

    [RelayCommand]
    private void ToggleBrowser()
    {
        IsBrowserVisible = !IsBrowserVisible;
    }
}
