using System;
using System.IO;
using System.Windows;
using Microsoft.Web.WebView2.Core;
using WhatsAppSender.App.ViewModels;

namespace WhatsAppSender.App
{
    public partial class GMapsScraperWindow : Window
    {
        public GMapsScraperWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
            InitializeWebView();
        }

        private async void InitializeWebView()
        {
            try
            {
                var userDataFolder = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "WhatsAppSenderPro", "GMapsWebView2");

                if (!Directory.Exists(userDataFolder))
                {
                    Directory.CreateDirectory(userDataFolder);
                }

                var env = await CoreWebView2Environment.CreateAsync(null, userDataFolder);
                await gmapsWebView.EnsureCoreWebView2Async(env);
                
                gmapsWebView.Source = new Uri("https://www.google.com/maps");

                if (DataContext is GMapsTabViewModel vm)
                {
                    vm.SetWebView(gmapsWebView);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"فشل تهيئة متصفح خرائط جوجل: {ex.Message}", "خطأ في تهيئة المتصفح", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
