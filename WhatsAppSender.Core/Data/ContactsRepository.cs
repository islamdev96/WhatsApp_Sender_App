using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Data.Sqlite;
using Dapper;
using WhatsAppSender.Core.Models;

namespace WhatsAppSender.Core.Data;

public class ContactsRepository
{
    private readonly Database _db;

    public ContactsRepository(Database db)
    {
        _db = db;
    }

    public List<ContactGroup> GetAll()
    {
        using var conn = _db.OpenConnection();
        var groups = conn.Query<ContactGroup>("SELECT id, name, created, updated FROM wa_groups ORDER BY id DESC").ToList();
        foreach (var g in groups)
        {
            g.Contacts = conn.Query<Contact>(
                "SELECT id, group_id as GroupId, phone, name FROM wa_contacts WHERE group_id = @GroupId ORDER BY id",
                new { GroupId = g.Id }).ToList();
        }
        return groups;
    }

    public List<string> GetNames()
    {
        using var conn = _db.OpenConnection();
        return conn.Query<string>("SELECT name FROM wa_groups ORDER BY id DESC").ToList();
    }

    public ContactGroup? GetByName(string name)
    {
        using var conn = _db.OpenConnection();
        var g = conn.QueryFirstOrDefault<ContactGroup>(
            "SELECT id, name, created, updated FROM wa_groups WHERE name = @Name",
            new { Name = name });
        if (g == null) return null;

        g.Contacts = conn.Query<Contact>(
            "SELECT id, group_id as GroupId, phone, name FROM wa_contacts WHERE group_id = @GroupId ORDER BY id",
            new { GroupId = g.Id }).ToList();
        return g;
    }

    public bool CreateGroup(string name, List<Contact>? contacts = null)
    {
        if (GetByName(name) != null) return false;

        var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
        using var conn = _db.OpenConnection();
        using var trans = conn.BeginTransaction();
        try
        {
            var groupId = conn.QuerySingle<int>(
                "INSERT INTO wa_groups (name, created, updated) VALUES (@Name, @Created, @Updated); SELECT last_insert_rowid();",
                new { Name = name, Created = now, Updated = now },
                transaction: trans);

            if (contacts != null && contacts.Any())
            {
                foreach (var c in contacts)
                {
                    conn.Execute(
                        "INSERT OR IGNORE INTO wa_contacts (group_id, phone, name) VALUES (@GroupId, @Phone, @Name)",
                        new { GroupId = groupId, Phone = c.Phone, Name = c.Name },
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

    public bool UpdateContacts(string name, List<Contact> contacts)
    {
        using var conn = _db.OpenConnection();
        var g = conn.QueryFirstOrDefault<ContactGroup>(
            "SELECT id FROM wa_groups WHERE name = @Name", new { Name = name });
        if (g == null) return false;

        using var trans = conn.BeginTransaction();
        try
        {
            conn.Execute("DELETE FROM wa_contacts WHERE group_id = @GroupId", new { GroupId = g.Id }, transaction: trans);
            foreach (var c in contacts)
            {
                conn.Execute(
                    "INSERT OR IGNORE INTO wa_contacts (group_id, phone, name) VALUES (@GroupId, @Phone, @Name)",
                    new { GroupId = g.Id, Phone = c.Phone, Name = c.Name },
                    transaction: trans);
            }

            var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
            conn.Execute("UPDATE wa_groups SET updated = @Updated WHERE id = @Id", new { Updated = now, Id = g.Id }, transaction: trans);
            trans.Commit();
            return true;
        }
        catch
        {
            trans.Rollback();
            return false;
        }
    }

    public int AddContacts(string name, List<Contact> newContacts)
    {
        using var conn = _db.OpenConnection();
        var g = conn.QueryFirstOrDefault<ContactGroup>(
            "SELECT id FROM wa_groups WHERE name = @Name", new { Name = name });
        if (g == null) return 0;

        using var trans = conn.BeginTransaction();
        try
        {
            var before = conn.QuerySingle<int>(
                "SELECT COUNT(*) FROM wa_contacts WHERE group_id = @GroupId", new { GroupId = g.Id }, transaction: trans);

            foreach (var c in newContacts)
            {
                conn.Execute(
                    "INSERT OR IGNORE INTO wa_contacts (group_id, phone, name) VALUES (@GroupId, @Phone, @Name)",
                    new { GroupId = g.Id, Phone = c.Phone, Name = c.Name },
                    transaction: trans);
            }

            var after = conn.QuerySingle<int>(
                "SELECT COUNT(*) FROM wa_contacts WHERE group_id = @GroupId", new { GroupId = g.Id }, transaction: trans);

            var added = after - before;
            if (added > 0)
            {
                var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
                conn.Execute("UPDATE wa_groups SET updated = @Updated WHERE id = @Id", new { Updated = now, Id = g.Id }, transaction: trans);
            }

            trans.Commit();
            return added;
        }
        catch
        {
            trans.Rollback();
            return 0;
        }
    }

    public bool AddContact(string groupName, string phone, string name = "")
    {
        var added = AddContacts(groupName, new List<Contact> { new() { Phone = phone, Name = name } });
        return added > 0;
    }

    public bool RemoveContact(string groupName, string phone)
    {
        using var conn = _db.OpenConnection();
        var g = conn.QueryFirstOrDefault<ContactGroup>(
            "SELECT id FROM wa_groups WHERE name = @Name", new { Name = groupName });
        if (g == null) return false;

        using var trans = conn.BeginTransaction();
        try
        {
            var rows = conn.Execute(
                "DELETE FROM wa_contacts WHERE group_id = @GroupId AND phone = @Phone",
                new { GroupId = g.Id, Phone = phone },
                transaction: trans);

            if (rows > 0)
            {
                var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
                conn.Execute("UPDATE wa_groups SET updated = @Updated WHERE id = @Id", new { Updated = now, Id = g.Id }, transaction: trans);
                trans.Commit();
                return true;
            }

            trans.Rollback();
            return false;
        }
        catch
        {
            trans.Rollback();
            return false;
        }
    }

    public void DeleteGroup(string name)
    {
        using var conn = _db.OpenConnection();
        conn.Execute("DELETE FROM wa_groups WHERE name = @Name", new { Name = name });
    }

    public bool RenameGroup(string oldName, string newName)
    {
        if (GetByName(newName) != null) return false;

        using var conn = _db.OpenConnection();
        var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm");
        var rows = conn.Execute(
            "UPDATE wa_groups SET name = @NewName, updated = @Updated WHERE name = @OldName",
            new { NewName = newName, Updated = now, OldName = oldName });
        return rows > 0;
    }

    public int GetContactCount(string name)
    {
        using var conn = _db.OpenConnection();
        var g = conn.QueryFirstOrDefault<ContactGroup>(
            "SELECT id FROM wa_groups WHERE name = @Name", new { Name = name });
        if (g == null) return 0;

        return conn.QuerySingle<int>(
            "SELECT COUNT(*) FROM wa_contacts WHERE group_id = @GroupId", new { GroupId = g.Id });
    }
}
