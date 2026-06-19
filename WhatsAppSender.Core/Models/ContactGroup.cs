using System;
using System.Collections.Generic;

namespace WhatsAppSender.Core.Models;

public class ContactGroup
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Created { get; set; } = string.Empty;
    public string Updated { get; set; } = string.Empty;

    // Navigation property
    public List<Contact> Contacts { get; set; } = new();
}
