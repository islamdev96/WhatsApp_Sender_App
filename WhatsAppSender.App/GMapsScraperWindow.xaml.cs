using System.Windows;

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
        }
    }
}
