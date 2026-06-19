using System.Windows;

namespace WhatsAppSender.App
{
    public partial class WarmerWindow : Window
    {
        public WarmerWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
