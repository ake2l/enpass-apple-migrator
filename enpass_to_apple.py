import csv
import re

def convert_to_otpauth(secret):
    if not secret:
        return ''
    secret = secret.upper()
    return f'otpauth://totp?secret={secret}&algorithm=SHA1&digits=6&period=30'

def transform_csv(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Split into records more reliably
    records = re.split(r'"\s+"', content.strip())
    
    with open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['Title', 'URL', 'Username', 'Password', 'Notes', 'OTPAuth'])
        
        for record in records:
            # Clean up the record
            record = record.strip().strip('"')
            
            # Split into fields
            parts = record.split('","')
            parts = [p.strip('"') for p in parts]
            
            # Initialize record data
            title = parts[0]
            url = ''
            username = ''
            password = ''
            notes = []
            totp = ''
            
            # Process fields in pairs
            for i in range(1, len(parts)-1, 2):
                key = parts[i]
                value = parts[i+1] if i+1 < len(parts) else ''
                
                if key == 'Username':
                    username = value
                elif key in ['Url', 'Website']:
                    if value:  # Only set URL if there's a value
                        url = value
                elif key == '*Password':
                    password = value
                elif key == 'Totp':
                    totp = value
                elif key and value:  # Only add non-empty key-value pairs to notes
                    notes.append(f"{key}: {value}")
            
            # Create notes string, filtering out empty entries
            notes_str = '; '.join(filter(None, notes))
            
            # Convert TOTP if present
            otpauth = convert_to_otpauth(totp) if totp else ''
            
            # Write the transformed record
            writer.writerow([
                title,
                url,
                username,
                password,
                notes_str,
                otpauth
            ])

# Usage
input_file = 'enpass-export.csv'
output_file = 'apple-import.csv'
transform_csv(input_file, output_file)
