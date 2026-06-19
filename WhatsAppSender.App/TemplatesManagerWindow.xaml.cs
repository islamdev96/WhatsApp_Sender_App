using System.Windows;

namespace WhatsAppSender.App
{
    public partial class TemplatesManagerWindow : Window
    {
        public TemplatesManagerWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
