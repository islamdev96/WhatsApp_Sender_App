using System;
using System.Collections.Generic;
using System.Linq;
using Dapper;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Data;

public class ScheduledCampaignsRepository
{
    private readonly Database _db;

    public ScheduledCampaignsRepository(Database db)
    {
        _db = db;
    }

    public List<ScheduledCampaign> GetAll()
    {
        using var conn = _db.OpenConnection();
        return conn.Query<ScheduledCampaign>(@"
            SELECT id, name, scheduled_time as ScheduledTime, message, attachments_json as AttachmentsJson, 
                   group_name as GroupName, contacts_json as ContactsJson, sending_mode as SendingMode, 
                   status, created_at as CreatedAt 
            FROM wa_scheduled_campaigns ORDER BY id DESC").ToList();
    }

    public List<ScheduledCampaign> GetUpcomingPending()
    {
        using var conn = _db.OpenConnection();
        return conn.Query<ScheduledCampaign>(@"
            SELECT id, name, scheduled_time as ScheduledTime, message, attachments_json as AttachmentsJson, 
                   group_name as GroupName, contacts_json as ContactsJson, sending_mode as SendingMode, 
                   status, created_at as CreatedAt 
            FROM wa_scheduled_campaigns 
            WHERE status = 'pending' ORDER BY scheduled_time ASC").ToList();
    }

    public int ScheduleCampaign(ScheduledCampaign sc)
    {
        var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        using var conn = _db.OpenConnection();
        return conn.QuerySingle<int>(@"
            INSERT INTO wa_scheduled_campaigns (
                name, scheduled_time, message, attachments_json, group_name, contacts_json, sending_mode, status, created_at
            ) VALUES (
                @Name, @ScheduledTime, @Message, @AttachmentsJson, @GroupName, @ContactsJson, @SendingMode, 'pending', @CreatedAt
            );
            SELECT last_insert_rowid();",
            new
            {
                Name = sc.Name,
                ScheduledTime = sc.ScheduledTime,
                Message = sc.Message,
                AttachmentsJson = sc.AttachmentsJson,
                GroupName = sc.GroupName,
                ContactsJson = sc.ContactsJson,
                SendingMode = sc.SendingMode,
                CreatedAt = now
            });
    }

    public bool UpdateStatus(int id, string status)
    {
        using var conn = _db.OpenConnection();
        var rows = conn.Execute(
            "UPDATE wa_scheduled_campaigns SET status = @Status WHERE id = @Id",
            new { Status = status, Id = id });
        return rows > 0;
    }

    public void Delete(int id)
    {
        using var conn = _db.OpenConnection();
        conn.Execute("DELETE FROM wa_scheduled_campaigns WHERE id = @Id", new { Id = id });
    }
}
