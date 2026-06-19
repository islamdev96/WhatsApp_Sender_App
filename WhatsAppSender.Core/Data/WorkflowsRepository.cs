using System;
using System.Collections.Generic;
using System.Linq;
using Dapper;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Data;

public class WorkflowsRepository
{
    private readonly Database _db;

    public WorkflowsRepository(Database db)
    {
        _db = db;
    }

    public List<Workflow> GetAll()
    {
        using var conn = _db.OpenConnection();
        var workflows = conn.Query<Workflow>("SELECT id, name, created, updated FROM wa_workflows ORDER BY id DESC").ToList();
        foreach (var w in workflows)
        {
            w.Steps = conn.Query<WorkflowStep>(@"
                SELECT id, workflow_id as WorkflowId, step_order as StepOrder, body, 
                       attachments_json as AttachmentsJson, delay_min as DelayMin, delay_max as DelayMax 
                FROM wa_workflow_steps WHERE workflow_id = @WorkflowId ORDER BY step_order", 
                new { WorkflowId = w.Id }).ToList();
        }
        return workflows;
    }

    public List<string> GetNames()
    {
        using var conn = _db.OpenConnection();
        return conn.Query<string>("SELECT name FROM wa_workflows ORDER BY id DESC").ToList();
    }

    public Workflow? GetByName(string name)
    {
        using var conn = _db.OpenConnection();
        var w = conn.QueryFirstOrDefault<Workflow>(
            "SELECT id, name, created, updated FROM wa_workflows WHERE name = @Name",
            new { Name = name });
        if (w == null) return null;

        w.Steps = conn.Query<WorkflowStep>(@"
            SELECT id, workflow_id as WorkflowId, step_order as StepOrder, body, 
                   attachments_json as AttachmentsJson, delay_min as DelayMin, delay_max as DelayMax 
            FROM wa_workflow_steps WHERE workflow_id = @WorkflowId ORDER BY step_order", 
            new { WorkflowId = w.Id }).ToList();
        return w;
    }

    public bool CreateWorkflow(string name, List<WorkflowStep>? steps = null)
    {
        if (GetByName(name) != null) return false;

        var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
        using var conn = _db.OpenConnection();
        using var trans = conn.BeginTransaction();
        try
        {
            var workflowId = conn.QuerySingle<int>(@"
                INSERT INTO wa_workflows (name, created, updated) VALUES (@Name, @Created, @Updated);
                SELECT last_insert_rowid();",
                new { Name = name, Created = now, Updated = now },
                transaction: trans);

            if (steps != null && steps.Any())
            {
                foreach (var s in steps)
                {
                    conn.Execute(@"
                        INSERT INTO wa_workflow_steps (workflow_id, step_order, body, attachments_json, delay_min, delay_max) 
                        VALUES (@WorkflowId, @StepOrder, @Body, @AttachmentsJson, @DelayMin, @DelayMax)",
                        new 
                        { 
                            WorkflowId = workflowId, 
                            StepOrder = s.StepOrder, 
                            Body = s.Body, 
                            AttachmentsJson = s.AttachmentsJson, 
                            DelayMin = s.DelayMin, 
                            DelayMax = s.DelayMax 
                        },
                        transaction: trans);
                }
            }

            trans.Commit();
            return true;
        }
        catch
        {
            trans.Rollback();
            throw;
        }
    }

    public bool UpdateWorkflow(string name, List<WorkflowStep> steps)
    {
        using var conn = _db.OpenConnection();
        var w = conn.QueryFirstOrDefault<Workflow>(
            "SELECT id FROM wa_workflows WHERE name = @Name", new { Name = name });
        if (w == null) return false;

        using var trans = conn.BeginTransaction();
        try
        {
            conn.Execute("DELETE FROM wa_workflow_steps WHERE workflow_id = @WorkflowId", new { WorkflowId = w.Id }, transaction: trans);
            foreach (var s in steps)
            {
                conn.Execute(@"
                    INSERT INTO wa_workflow_steps (workflow_id, step_order, body, attachments_json, delay_min, delay_max) 
                    VALUES (@WorkflowId, @StepOrder, @Body, @AttachmentsJson, @DelayMin, @DelayMax)",
                    new 
                    { 
                        WorkflowId = w.Id, 
                        StepOrder = s.StepOrder, 
                        Body = s.Body, 
                        AttachmentsJson = s.AttachmentsJson, 
                        DelayMin = s.DelayMin, 
                        DelayMax = s.DelayMax 
                    },
                    transaction: trans);
            }

            var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
            conn.Execute("UPDATE wa_workflows SET updated = @Updated WHERE id = @Id", new { Updated = now, Id = w.Id }, transaction: trans);
            trans.Commit();
            return true;
        }
        catch
        {
            trans.Rollback();
            return false;
        }
    }

    public void DeleteWorkflow(string name)
    {
        using var conn = _db.OpenConnection();
        conn.Execute("DELETE FROM wa_workflows WHERE name = @Name", new { Name = name });
    }
}
