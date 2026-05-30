"""Text and message parsing helpers for anti-ban functionality."""
import re
import random


def parse_spintax(text: str) -> str:
    """Parses spintax in the format {choice1|choice2|choice3} recursively.
    
    Example:
        "{Hello|Hi|Hey} {dear|friend}, how are you?" -> "Hello friend, how are you?"
    """
    if not text:
        return ""
    pattern = re.compile(r'\{([^{}]+)\}')
    # Loop to parse nested spintax from the inside out
    while True:
        match = pattern.search(text)
        if not match:
            break
        choices = match.group(1).split('|')
        text = text[:match.start()] + random.choice(choices) + text[match.end():]
    return text
