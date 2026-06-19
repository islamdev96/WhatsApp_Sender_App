namespace WhatsAppSender.Core.Models;

public class Contact
{
    public int Id { get; set; }
    public int GroupId { get; set; }
    public string Phone { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
}
