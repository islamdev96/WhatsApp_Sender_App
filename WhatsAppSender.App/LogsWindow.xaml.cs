using System.Windows;

namespace WhatsAppSender.App
{
    public partial class LogsWindow : Window
    {
        public LogsWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
