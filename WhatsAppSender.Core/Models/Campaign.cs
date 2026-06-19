using System;
using System.Collections.Generic;

namespace WhatsAppSender.Core.Models;

public class Campaign
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Date { get; set; } = string.Empty;
    public int Total { get; set; }
    public int Sent { get; set; }
    public int Failed { get; set; }
    public int Invalid { get; set; }
    public int DurationSeconds { get; set; }
    public double SuccessRate { get; set; }
    public string CsvPath { get; set; } = string.Empty;

    public List<CampaignResult> Results { get; set; } = new();
}

public class CampaignResult
{
    public int Id { get; set; }
    public int CampaignId { get; set; }
    public string Phone { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty; // e.g., Sent, Failed, Invalid
    public string ErrorCode { get; set; } = string.Empty;
    public string Timestamp { get; set; } = string.Empty;
}
