using System.Configuration;
using System.Data;
using System.Windows;

namespace WhatsAppSender.App;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
    public static void ChangeLanguage(string langCode)
    {
        var app = (App)Current;
        var dicts = app.Resources.MergedDictionaries;
        
        ResourceDictionary? existingLang = null;
        foreach (var dict in dicts)
        {
            if (dict.Source != null && (dict.Source.OriginalString.Contains("Ar.xaml") || dict.Source.OriginalString.Contains("En.xaml")))
            {
                existingLang = dict;
                break;
            }
        }

        if (existingLang != null)
        {
            dicts.Remove(existingLang);
        }

        var newLang = new ResourceDictionary
        {
            Source = new Uri($"Resources/{langCode}.xaml", UriKind.Relative)
        };
        dicts.Add(newLang);
    }

    public static void ChangeTheme(string themeName)
    {
        var app = (App)Current;
        var dicts = app.Resources.MergedDictionaries;
        
        ResourceDictionary? existingTheme = null;
        foreach (var dict in dicts)
        {
            if (dict.Source != null && (dict.Source.OriginalString.Contains("DarkTheme.xaml") || dict.Source.OriginalString.Contains("LightTheme.xaml")))
            {
                existingTheme = dict;
                break;
            }
        }

        if (existingTheme != null)
        {
            dicts.Remove(existingTheme);
        }

        var newTheme = new ResourceDictionary
        {
            Source = new Uri($"Themes/{themeName}Theme.xaml", UriKind.Relative)
        };
        dicts.Insert(0, newTheme);
    }
}

