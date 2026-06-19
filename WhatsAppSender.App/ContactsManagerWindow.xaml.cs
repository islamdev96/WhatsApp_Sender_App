using System.Windows;

namespace WhatsAppSender.App
{
    public partial class ContactsManagerWindow : Window
    {
        public ContactsManagerWindow()
        {
            InitializeComponent();
            if (Application.Current.MainWindow != null)
            {
                FlowDirection = Application.Current.MainWindow.FlowDirection;
            }
        }
    }
}
