using System;
using System.IO;
using System.Windows;
using Microsoft.Web.WebView2.Core;
using WhatsAppSender.App.ViewModels;

namespace WhatsAppSender.App;

/// <summary>
/// Interaction logic for MainWindow.xaml
/// </summary>
public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();

        var viewModel = new MainWindowViewModel();
        DataContext = viewModel;

        // Initialize Edge WebView2 asynchronously
        InitializeWebView(viewModel);
    }

    private async void InitializeWebView(MainWindowViewModel viewModel)
    {
        try
        {
            // Build the local application user data folder to persist sessions (avoid scanning QR code every time)
            var userDataFolder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "WhatsAppSenderPro", "WebView2");

            if (!Directory.Exists(userDataFolder))
            {
                Directory.CreateDirectory(userDataFolder);
            }

            var env = await CoreWebView2Environment.CreateAsync(null, userDataFolder);
            
            // Ensure WebView2 is initialized
            await webView.EnsureCoreWebView2Async(env);

            // Set the source programmatically
            webView.Source = new Uri("https://web.whatsapp.com");

            // Link the initialized CoreWebView2 instance to our automation service
            viewModel.WhatsAppService.SetCoreWebView2(webView.CoreWebView2);
            
            viewModel.LogsTab.AddLog("INFO", "Edge WebView2 initialized and linked successfully.");
        }
        catch (Exception ex)
        {
            viewModel.LogsTab.AddLog("ERROR", $"WebView2 initialization failed: {ex.Message}");
            MessageBox.Show(
                $"فشل تهيئة متصفح واتساب: {ex.Message}\n\nيرجى التأكد من تثبيت WebView2 Runtime على جهازك.",
                "خطأ في تهيئة المتصفح / Browser Init Error",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
        }
    }
}