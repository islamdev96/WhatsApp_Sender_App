"""Phone number normalization utilities."""
import re


def _normalize_phone(phone, default_country_code="20"):
    """Normalize a phone number string.

    Handles:
    - Leading '+' sign (strips it for WhatsApp API)
    - Numbers already starting with country code
    - Egypt-specific local formats (01X → 201X) when default is '20'
    - Generic local numbers with configurable default country code
    """
    if not phone:
        return None
    phone = str(phone).strip()
    # Remove .0 from float conversion
    if phone.endswith('.0'):
        phone = phone[:-2]
    # Remove common formatting chars
    phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
    # Handle + prefix
    if phone.startswith('+'):
        phone = phone[1:]
    
    # Smart generic normalizing: if a local number starts with 0 (e.g. 05xxx or 01xxx)
    # and default_country_code is set, strip the leading 0 and prepend the country code.
    if default_country_code:
        default_cc = str(default_country_code).strip().replace("+", "")
        if phone.startswith('0') and not phone.startswith('00') and len(phone) > 4:
            phone = default_cc + phone[1:]

    # If already starts with country code, return as-is
    if default_country_code and phone.startswith(str(default_country_code)):
        return phone
    # Egypt-specific: local mobile numbers
    if default_country_code == "20":
        if phone.startswith('01') and len(phone) == 11:
            return '2' + phone
        if phone.startswith('1') and len(phone) == 10:
            return '20' + phone
    # Generic: prepend default country code for short local numbers
    if default_country_code and len(phone) <= 10 and not phone.startswith('0'):
        return str(default_country_code) + phone
    return phone



def normalize_phone(phone: str, default_country_code="20") -> str:
    """Public wrapper for phone normalization."""
    return _normalize_phone(phone, default_country_code)


