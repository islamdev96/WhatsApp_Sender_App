using System;

namespace WhatsAppSender.Core.Models;

public class Template
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Body { get; set; } = string.Empty;
    public string Created { get; set; } = string.Empty;
    public string Updated { get; set; } = string.Empty;
}
