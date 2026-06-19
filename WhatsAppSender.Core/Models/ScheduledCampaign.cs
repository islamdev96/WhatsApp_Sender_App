using System;

namespace WhatsAppSender.Core.Models;

public class ScheduledCampaign
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string ScheduledTime { get; set; } = string.Empty; // Format: YYYY-MM-DD HH:MM
    public string Message { get; set; } = string.Empty;
    public string AttachmentsJson { get; set; } = string.Empty;
    public string GroupName { get; set; } = string.Empty;
    public string ContactsJson { get; set; } = string.Empty;
    public string SendingMode { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty; // e.g., pending, sending, completed, failed, cancelled
    public string CreatedAt { get; set; } = string.Empty;
}
