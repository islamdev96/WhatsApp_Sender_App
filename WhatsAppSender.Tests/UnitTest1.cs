using Xunit;
using System;
using System.Reflection;
using System.Linq;

namespace WhatsAppSender.Tests;

public class UnitTest1
{
    [Fact]
    public void Test1()
    {
        var assembly = Assembly.Load("Microsoft.Web.WebView2.Core");
        var types = assembly.GetTypes()
            .Where(t => t.Name.Contains("File") || t.Name.Contains("Dialog"))
            .Select(t => t.FullName)
            .ToList();
        
        foreach (var type in types)
        {
            // Write to test runner output
            Assert.True(true, type);
        }
    }
}