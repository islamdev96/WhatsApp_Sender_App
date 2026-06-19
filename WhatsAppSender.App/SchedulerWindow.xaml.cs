using System.Windows;

namespace WhatsAppSender.App
{
    public partial class SchedulerWindow : Window
    {
        public SchedulerWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
