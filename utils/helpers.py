import csv
import os

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
                
                # Try multiple possible column names for phone and name
                phone = normalized_row.get('phone') or normalized_row.get('mobile') or \
                        normalized_row.get('number') or normalized_row.get('phone 1 - value')
                name = normalized_row.get('name') or normalized_row.get('given name') or 'Customer'
                
                if phone:
                    phone = phone.strip().replace(' ', '').replace('-', '')
                    # Egypt specific formatting
                    if phone.startswith('01'):
                        phone = '2' + phone
                    elif phone.startswith('1') and len(phone) == 10:
                        phone = '20' + phone
                        
                    contacts.append({'phone': phone, 'name': name})
    except Exception as e:
        print(f"Error reading CSV: {e}")
        
    return contacts

def create_contacts_template(file_path):
    """Creates a sample CSV template for the user."""
    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Phone'])
            writer.writerow(['Client Name', '010XXXXXXXX'])
        return True
    except:
        return False
