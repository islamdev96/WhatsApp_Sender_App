import csv
import os
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
    # Remove common formatting chars
    phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
    # Remove .0 from float conversion
    if phone.endswith('.0'):
        phone = phone[:-2]
    # Handle + prefix
    if phone.startswith('+'):
        phone = phone[1:]
    # If already starts with country code, return as-is
    if default_country_code and phone.startswith(default_country_code):
        return phone
    # Egypt-specific: local mobile numbers
    if default_country_code == "20":
        if phone.startswith('01') and len(phone) == 11:
            return '2' + phone
        if phone.startswith('1') and len(phone) == 10:
            return '20' + phone
    # Generic: prepend default country code for short local numbers
    if default_country_code and len(phone) <= 10 and not phone.startswith('0'):
        return default_country_code + phone
    return phone


def normalize_phone(phone, default_country_code="20"):
    """Public wrapper for phone normalization."""
    return _normalize_phone(phone, default_country_code)


def read_contacts(file_path):
    """Reads contacts from a CSV file and returns a list of dictionaries."""
    contacts = []
    try:
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                normalized_row = {k.strip().lower(): v for k, v in row.items()}

                phone = normalized_row.get('phone') or normalized_row.get('mobile') or \
                        normalized_row.get('number') or normalized_row.get('phone 1 - value')
                name = normalized_row.get('name') or normalized_row.get('given name') or 'Customer'
                var1 = normalized_row.get('var1') or normalized_row.get('variable1') or normalized_row.get('v1')
                var2 = normalized_row.get('var2') or normalized_row.get('variable2') or normalized_row.get('v2')
                var3 = normalized_row.get('var3') or normalized_row.get('variable3') or normalized_row.get('v3')
                var4 = normalized_row.get('var4') or normalized_row.get('variable4') or normalized_row.get('v4')
                var5 = normalized_row.get('var5') or normalized_row.get('variable5') or normalized_row.get('v5')

                phone = _normalize_phone(phone)
                if phone:
                    c = {'phone': phone, 'name': name.strip()}
                    if var1: c['var1'] = var1
                    if var2: c['var2'] = var2
                    if var3: c['var3'] = var3
                    if var4: c['var4'] = var4
                    if var5: c['var5'] = var5
                    contacts.append(c)
    except Exception as e:
        print(f"Error reading CSV: {e}")

    return contacts


def read_contacts_excel(file_path):
    """Reads contacts from an Excel (.xlsx) file."""
    contacts = []
    try:
        import openpyxl
        if not os.path.exists(file_path):
            return []

        wb = openpyxl.load_workbook(file_path, read_only=True)
        ws = wb.active

        # Read header row
        headers = []
        for cell in next(ws.iter_rows(min_row=1, max_row=1)):
            headers.append(str(cell.value or '').strip().lower())

        # Find phone and name columns
        phone_col = None
        name_col = None
        for i, h in enumerate(headers):
            if h in ('phone', 'mobile', 'number', 'phone 1 - value', 'رقم', 'هاتف'):
                phone_col = i
            if h in ('name', 'given name', 'اسم', 'الاسم'):
                name_col = i
        var_cols = {}
        for i, h in enumerate(headers):
            if h in ('var1', 'variable1', 'v1'):
                var_cols['var1'] = i
            if h in ('var2', 'variable2', 'v2'):
                var_cols['var2'] = i
            if h in ('var3', 'variable3', 'v3'):
                var_cols['var3'] = i
            if h in ('var4', 'variable4', 'v4'):
                var_cols['var4'] = i
            if h in ('var5', 'variable5', 'v5'):
                var_cols['var5'] = i

        if phone_col is None:
            # Try first two columns: assume col 0=name, col 1=phone
            if len(headers) >= 2:
                name_col = 0
                phone_col = 1
            elif len(headers) == 1:
                phone_col = 0

        if phone_col is None:
            return []

        for row in ws.iter_rows(min_row=2):
            phone_val = row[phone_col].value if phone_col < len(row) else None
            name_val = row[name_col].value if name_col is not None and name_col < len(row) else 'Customer'

            phone = _normalize_phone(phone_val)
            if phone:
                c = {'phone': phone, 'name': str(name_val or 'Customer').strip()}
                for k, idx in var_cols.items():
                    if idx < len(row):
                        val = row[idx].value
                        if val is not None:
                            c[k] = str(val)
                contacts.append(c)

        wb.close()
    except Exception as e:
        print(f"Error reading Excel: {e}")

    return contacts


def read_contacts_auto(file_path):
    """Auto-detect file type and read contacts accordingly."""
    if not file_path or not os.path.exists(file_path):
        return []
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ('.xlsx', '.xls'):
        return read_contacts_excel(file_path)
    else:
        return read_contacts(file_path)


def create_contacts_template(file_path):
    """Creates a sample CSV template for the user."""
    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Phone', 'Var1', 'Var2', 'Var3', 'Var4', 'Var5'])
            writer.writerow(['Client Name', '010XXXXXXXX', 'Value1', 'Value2', 'Value3', 'Value4', 'Value5'])
        return True
    except Exception:
        return False
