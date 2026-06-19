using System;
using System.Text.RegularExpressions;

namespace WhatsAppSender.Core.Services;

public class SpintaxEngine
{
    private static readonly Regex Pattern = new(@"\{([^{}]+)\}", RegexOptions.Compiled);
    private readonly Random _rng = new();

    public string Parse(string text)
    {
        if (string.IsNullOrEmpty(text))
        {
            return string.Empty;
        }

        // Parse nested spintax from the inside out
        while (true)
        {
            var match = Pattern.Match(text);
            if (!match.Success)
            {
                break;
            }

            var choices = match.Groups[1].Value.Split('|');
            var selected = choices[_rng.Next(choices.Length)];
            text = text.Substring(0, match.Index) + selected + text.Substring(match.Index + match.Length);
        }

        return text;
    }
}
