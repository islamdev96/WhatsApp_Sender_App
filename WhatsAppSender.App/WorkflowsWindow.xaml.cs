using System.Windows;

namespace WhatsAppSender.App
{
    public partial class WorkflowsWindow : Window
    {
        public WorkflowsWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
