using System;
using System.Collections.Generic;

namespace WhatsAppSender.Core.Models;

public class Workflow
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Created { get; set; } = string.Empty;
    public string Updated { get; set; } = string.Empty;

    public List<WorkflowStep> Steps { get; set; } = new();
}

public class WorkflowStep
{
    public int Id { get; set; }
    public int WorkflowId { get; set; }
    public int StepOrder { get; set; }
    public string Body { get; set; } = string.Empty;
    public string AttachmentsJson { get; set; } = string.Empty; // Store as serialized JSON
    public int DelayMin { get; set; }
    public int DelayMax { get; set; }
}
