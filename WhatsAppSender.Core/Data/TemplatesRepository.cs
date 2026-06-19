using System;
using System.Collections.Generic;
using System.Linq;
using Dapper;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Data;

public class TemplatesRepository
{
    private readonly Database _db;

    public TemplatesRepository(Database db)
    {
        _db = db;
    }

    public List<Template> GetAll()
    {
        using var conn = _db.OpenConnection();
        return conn.Query<Template>("SELECT id, name, body, created, updated FROM wa_templates ORDER BY id DESC").ToList();
    }

    public List<string> GetNames()
    {
        using var conn = _db.OpenConnection();
        return conn.Query<string>("SELECT name FROM wa_templates ORDER BY id DESC").ToList();
    }

    public Template? GetByName(string name)
    {
        using var conn = _db.OpenConnection();
        return conn.QueryFirstOrDefault<Template>(
            "SELECT id, name, body, created, updated FROM wa_templates WHERE name = @Name",
            new { Name = name });
    }

    public void Add(string name, string body)
    {
        var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
        using var conn = _db.OpenConnection();
        var existing = conn.QueryFirstOrDefault<int?>(
            "SELECT id FROM wa_templates WHERE name = @Name", new { Name = name });

        if (existing.HasValue)
        {
            conn.Execute(
                "UPDATE wa_templates SET body = @Body, updated = @Updated WHERE name = @Name",
                new { Body = body, Updated = now, Name = name });
        }
        else
        {
            conn.Execute(
                "INSERT INTO wa_templates (name, body, created, updated) VALUES (@Name, @Body, @Created, @Updated)",
                new { Name = name, Body = body, Created = now, Updated = now });
        }
    }

    public void Delete(string name)
    {
        using var conn = _db.OpenConnection();
        conn.Execute("DELETE FROM wa_templates WHERE name = @Name", new { Name = name });
    }

    public void Rename(string oldName, string newName)
    {
        var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
        using var conn = _db.OpenConnection();
        conn.Execute(
            "UPDATE wa_templates SET name = @NewName, updated = @Updated WHERE name = @OldName",
            new { NewName = newName, Updated = now, OldName = oldName });
    }
}
