using System.Windows;

namespace WhatsAppSender.App
{
    public partial class CampaignsHistoryWindow : Window
    {
        public CampaignsHistoryWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
