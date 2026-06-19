using System;
using System.Collections.Generic;
using System.Linq;
using Dapper;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Data;

public class CampaignsRepository
{
    private readonly Database _db;

    public CampaignsRepository(Database db)
    {
        _db = db;
    }

    public List<Campaign> GetAll()
    {
        using var conn = _db.OpenConnection();
        var campaigns = conn.Query<Campaign>(@"
            SELECT id, name, date, total, sent, failed, invalid, 
                   duration_seconds as DurationSeconds, success_rate as SuccessRate, csv_path as CsvPath 
            FROM wa_campaigns ORDER BY id DESC").ToList();
        return campaigns;
    }

    public Campaign? GetById(int id)
    {
        using var conn = _db.OpenConnection();
        var campaign = conn.QueryFirstOrDefault<Campaign>(@"
            SELECT id, name, date, total, sent, failed, invalid, 
                   duration_seconds as DurationSeconds, success_rate as SuccessRate, csv_path as CsvPath 
            FROM wa_campaigns WHERE id = @Id", new { Id = id });
        if (campaign == null) return null;

        campaign.Results = conn.Query<CampaignResult>(@"
            SELECT id, campaign_id as CampaignId, phone, name, status, error_code as ErrorCode, timestamp 
            FROM wa_campaign_results WHERE campaign_id = @CampaignId ORDER BY id", 
            new { CampaignId = id }).ToList();

        return campaign;
    }

    public int CreateCampaign(Campaign c)
    {
        using var conn = _db.OpenConnection();
        using var trans = conn.BeginTransaction();
        try
        {
            var campaignId = conn.QuerySingle<int>(@"
                INSERT INTO wa_campaigns (name, date, total, sent, failed, invalid, duration_seconds, success_rate, csv_path) 
                VALUES (@Name, @Date, @Total, @Sent, @Failed, @Invalid, @DurationSeconds, @SuccessRate, @CsvPath);
                SELECT last_insert_rowid();",
                new 
                { 
                    Name = c.Name, 
                    Date = c.Date, 
                    Total = c.Total, 
                    Sent = c.Sent, 
                    Failed = c.Failed, 
                    Invalid = c.Invalid, 
                    DurationSeconds = c.DurationSeconds, 
                    SuccessRate = c.SuccessRate, 
                    CsvPath = c.CsvPath 
                },
                transaction: trans);

            if (c.Results != null && c.Results.Any())
            {
                foreach (var r in c.Results)
                {
                    conn.Execute(@"
                        INSERT INTO wa_campaign_results (campaign_id, phone, name, status, error_code, timestamp) 
                        VALUES (@CampaignId, @Phone, @Name, @Status, @ErrorCode, @Timestamp)",
                        new 
                        { 
                            CampaignId = campaignId, 
                            Phone = r.Phone, 
                            Name = r.Name, 
                            Status = r.Status, 
                            ErrorCode = r.ErrorCode, 
                            Timestamp = r.Timestamp 
                        },
                        transaction: trans);
                }
            }

            trans.Commit();
            return campaignId;
        }
        catch
        {
            trans.Rollback();
            throw;
        }
    }

    public void AddCampaignResult(CampaignResult r)
    {
        using var conn = _db.OpenConnection();
        conn.Execute(@"
            INSERT INTO wa_campaign_results (campaign_id, phone, name, status, error_code, timestamp) 
            VALUES (@CampaignId, @Phone, @Name, @Status, @ErrorCode, @Timestamp)",
            new 
            { 
                CampaignId = r.CampaignId, 
                Phone = r.Phone, 
                Name = r.Name, 
                Status = r.Status, 
                ErrorCode = r.ErrorCode, 
                Timestamp = r.Timestamp 
            });

        // Update campaign numbers dynamically
        using var trans = conn.BeginTransaction();
        try
        {
            var statusCol = r.Status.ToLower() switch
            {
                "sent" or "success" => "sent = sent + 1",
                "invalid" => "invalid = invalid + 1",
                _ => "failed = failed + 1"
            };

            conn.Execute($"UPDATE wa_campaigns SET {statusCol} WHERE id = @CampaignId", new { CampaignId = r.CampaignId }, transaction: trans);

            // Re-calculate success rate
            var stats = conn.QueryFirstOrDefault(@"
                SELECT total, sent, failed, invalid FROM wa_campaigns WHERE id = @CampaignId", 
                new { CampaignId = r.CampaignId }, 
                transaction: trans);

            if (stats != null)
            {
                int total = stats.total;
                int sent = stats.sent;
                double rate = total > 0 ? (double)sent / total * 100.0 : 0.0;
                conn.Execute(@"
                    UPDATE wa_campaigns SET success_rate = @Rate WHERE id = @CampaignId", 
                    new { Rate = rate, CampaignId = r.CampaignId }, 
                    transaction: trans);
            }

            trans.Commit();
        }
        catch
        {
            trans.Rollback();
            throw;
        }
    }

    public void DeleteCampaign(int id)
    {
        using var conn = _db.OpenConnection();
        conn.Execute("DELETE FROM wa_campaigns WHERE id = @Id", new { Id = id });
    }

    public void UpdateCampaignDuration(int id, int durationSeconds)
    {
        using var conn = _db.OpenConnection();
        conn.Execute("UPDATE wa_campaigns SET duration_seconds = @DurationSeconds WHERE id = @Id", 
            new { DurationSeconds = durationSeconds, Id = id });
    }
}

