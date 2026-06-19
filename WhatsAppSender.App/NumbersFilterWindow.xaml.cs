using System.Windows;

namespace WhatsAppSender.App
{
    public partial class NumbersFilterWindow : Window
    {
        public NumbersFilterWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
