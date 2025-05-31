import csv
import re
import urllib.parse
import json
from typing import List, Dict, Set
import typer
import itertools

# --- Configuration for Enpass Field Mapping ---
# Add known Enpass column names (case-insensitive) that map to Apple fields.
# The script will try these in order. First one found will be used.
ENPASS_FIELD_MAPPINGS: Dict[str, List[str]] = {
    'Title': ['Title', 'Name', 'Login name', 'ItemName'],
    'URL': ['URL', 'Website', 'Web Address', 'Login URL'],
    'Username': ['Username', 'User ID', 'Login ID', 'Login Username'],
    'Password': ['Password', '*Password', 'Passphrase', 'Login Password'],
    'TOTP': ['TOTP', 'TOTP Secret', 'One-Time Password', 'OTP Secret', 'OTP', 'TOTP Key'],
    'Notes': ['Note', 'Notes', 'Description', 'Details', 'Memo'] # Primary notes field from Enpass
}

# Apple Passwords CSV Header
APPLE_CSV_HEADER: List[str] = ['Title', 'URL', 'Username', 'Password', 'Notes', 'OTPAuth']

def generate_otpauth_url(secret_key: str, title: str = "", username: str = "") -> str:
    """Generates an otpauth://totp URL for use with authenticator apps.

    Args:
        secret_key: The Base32 encoded TOTP secret key.
        title: The title of the account or service (can be used as issuer).
        username: The username or account identifier.

    Returns:
        A string representing the otpauth://totp URL, or an empty string
        if the secret_key is empty.
    """
    if not secret_key:
        return ""

    cleaned_secret = secret_key.replace(" ", "").upper()
    # Basic check for Base32 characters. A more robust validation might be needed
    # if secrets can come in various non-standard formats.
    if not re.fullmatch(r"[A-Z2-7=]+", cleaned_secret):
        print(f"Warning: TOTP secret for '{title if title else username}' "
              f"('{secret_key[:10]}...') contains potentially invalid characters. "
              f"OTPAuth URL might be invalid.")
        # Depending on strictness, one might return "" or proceed.
        # Let's proceed but with the potentially problematic secret.

    # Construct the label for the OTPAuth URL.
    # Apple Passwords often uses Title for issuer and Username for account.
    # Format: Issuer:AccountName or just AccountName
    issuer_name = title.strip()
    account_name = username.strip()

    if issuer_name and account_name:
        label = f"{issuer_name}:{account_name}"
    elif account_name:
        label = account_name
    elif issuer_name: # Less common to have issuer without account, but possible
        label = issuer_name
    else:
        label = "UnknownAccount"
    
    encoded_label = urllib.parse.quote(label)

    params = {
        'secret': cleaned_secret,
        'algorithm': 'SHA1', # Common default
        'digits': '6',     # Common default
        'period': '30'     # Common default
    }
    if issuer_name: # Add issuer parameter, helpful for many authenticators
        params['issuer'] = issuer_name

    query_string = urllib.parse.urlencode(params)
    
    return f"otpauth://totp/{encoded_label}?{query_string}"


def transform_enpass_csv_to_apple(input_filepath: str, output_filepath: str) -> None:
    """Converts an Enpass CSV export file to an Apple Passwords compatible CSV file.

    This function reads an Enpass CSV, maps known fields to Apple's expected
    format (Title, URL, Username, Password, OTPAuth URL, Notes), generates
    OTPAuth URLs from TOTP secrets, and consolidates any unmapped Enpass
    fields into the 'Notes' column of the output CSV.

    The Enpass CSV is expected to have a header row. Field names are matched
    case-insensitively based on `ENPASS_FIELD_MAPPINGS`.

    Args:
        input_filepath: Path to the Enpass CSV export file.
        output_filepath: Path where the Apple Passwords compatible CSV will be saved.

    Raises:
        FileNotFoundError: If the input_filepath does not exist.
        IOError: If there are issues reading the input file or writing the output file.
        csv.Error: If the input CSV is malformed or the header is not found.
        Exception: For other unexpected errors during processing.
    """
    print(f"Starting conversion from '{input_filepath}' to '{output_filepath}'...")

    try:
        with open(input_filepath, 'r', encoding='utf-8-sig') as infile, \
             open(output_filepath, 'w', newline='', encoding='utf-8') as outfile:

            csv_reader = csv.reader(infile)
            csv_writer = csv.writer(outfile)

            csv_writer.writerow(APPLE_CSV_HEADER)

            try:
                enpass_header_original: List[str] = next(csv_reader)
            except StopIteration:
                print(f"Error: Input CSV file '{input_filepath}' is empty or has no header row.")
                raise csv.Error("CSV file has no header row.") from None
            
            # Detect key-value export (no real header row) by checking first cell
            header_first = enpass_header_original[0].strip()
            title_opts_lower = [opt.lower() for opt in ENPASS_FIELD_MAPPINGS['Title']]
            if header_first.lower() not in title_opts_lower:
                # Key-value CSV export: each row is Title followed by alternating label/value cells
                for row in itertools.chain([enpass_header_original], csv_reader):
                    title = row[0].strip()
                    entry: Dict[str, str] = {'Title': title, 'Notes': ''}
                    extra_notes: List[str] = []
                    # Process label/value pairs
                    for i in range(1, len(row), 2):
                        label = row[i].strip()
                        value = row[i+1].strip() if i+1 < len(row) else ''
                        if not label or not value:
                            continue
                        mapped = False
                        for apple_key2, options2 in ENPASS_FIELD_MAPPINGS.items():
                            if label in options2:
                                entry[apple_key2] = value
                                mapped = True
                                break
                        if not mapped:
                            extra_notes.append(f"{label}: {value}")
                    otpauth_url = generate_otpauth_url(entry.get('TOTP', ''), title, entry.get('Username', ''))
                    consolidated_notes = '\n'.join(filter(None, [entry.get('Notes', ''), *extra_notes]))
                    csv_writer.writerow([
                        title,
                        entry.get('URL', ''),
                        entry.get('Username', ''),
                        entry.get('Password', ''),
                        consolidated_notes,
                        otpauth_url
                    ])
                return
             
            enpass_header_stripped: List[str] = [h.strip() for h in enpass_header_original]
            enpass_header_lower: List[str] = [h.lower() for h in enpass_header_stripped]
             
            header_to_index: Dict[str, int] = {name_lower: i for i, name_lower in enumerate(enpass_header_lower)}

            apple_field_indices: Dict[str, int] = {} # Maps Apple field name to Enpass column index
            mapped_enpass_col_indices: Set[int] = set()

            for apple_key, enpass_options in ENPASS_FIELD_MAPPINGS.items():
                 found_index = -1
                 for option in enpass_options:
                     option_lower = option.lower()
                     if option_lower in header_to_index:
                         found_index = header_to_index[option_lower]
                         # Only add to mapped_enpass_col_indices if it's not already used by another primary mapping
                         # This prevents, for example, a generic "Name" field being consumed by "Title"
                         # and then also by "Username" if "Name" was an option for both.
                         # The first ENPASS_FIELD_MAPPINGS key to match a column takes precedence for that column.
                         if found_index not in mapped_enpass_col_indices:
                              mapped_enpass_col_indices.add(found_index)
                         break 
                 apple_field_indices[apple_key] = found_index
                 if found_index == -1:
                     print(f"Info: No direct column found in Enpass CSV for Apple field '{apple_key}' "
                           f"using mapping options: {enpass_options}.")

            # If no primary mapping found, treat as key-value export format
            if not mapped_enpass_col_indices:
                 # Key-value CSV export: each row is Title followed by alternating label/value cells
                 for row in itertools.chain([enpass_header_original], csv_reader):
                     title = row[0].strip()
                     entry: Dict[str, str] = {'Title': title, 'Notes': ''}
                     extra_notes: List[str] = []
                     # Process label/value pairs
                     for i in range(1, len(row), 2):
                         label = row[i].strip()
                         value = row[i+1].strip() if i+1 < len(row) else ''
                         if not label or not value:
                             continue
                         mapped = False
                         for apple_key2, options2 in ENPASS_FIELD_MAPPINGS.items():
                             if label in options2:
                                 entry[apple_key2] = value
                                 mapped = True
                                 break
                         if not mapped:
                             extra_notes.append(f"{label}: {value}")
                     otpauth_url = generate_otpauth_url(entry.get('TOTP', ''), title, entry.get('Username', ''))
                     consolidated_notes = '\n'.join(filter(None, [entry.get('Notes', ''), *extra_notes]))
                     csv_writer.writerow([
                         title,
                         entry.get('URL', ''),
                         entry.get('Username', ''),
                         entry.get('Password', ''),
                         consolidated_notes,
                         otpauth_url
                     ])
                 return
             
            processed_rows = 0
            for row_num, row_data in enumerate(csv_reader, start=2):
                if not any(field.strip() for field in row_data):
                    print(f"Info: Skipping empty row {row_num}.")
                    continue

                if len(row_data) < len(enpass_header_original):
                    row_data.extend([''] * (len(enpass_header_original) - len(row_data)))
                elif len(row_data) > len(enpass_header_original):
                    print(f"Warning: Row {row_num} has more columns ({len(row_data)}) than header "
                          f"({len(enpass_header_original)}). Extra data will be ignored if unnamed.")
                    row_data = row_data[:len(enpass_header_original)]


                def get_field_value(apple_key: str) -> str:
                    idx = apple_field_indices.get(apple_key, -1)
                    return row_data[idx].strip() if idx != -1 and idx < len(row_data) else ""

                title_val = get_field_value('Title')
                url_val = get_field_value('URL')
                username_val = get_field_value('Username')
                # Passwords should generally not be stripped of leading/trailing whitespace
                password_idx = apple_field_indices.get('Password', -1)
                password_val = row_data[password_idx] if password_idx != -1 and password_idx < len(row_data) else ""
                
                totp_secret_val = get_field_value('TOTP')
                enpass_notes_val = get_field_value('Notes')

                otpauth_url = generate_otpauth_url(totp_secret_val, title_val, username_val)

                additional_notes_list: List[str] = []
                if enpass_notes_val:
                    additional_notes_list.append(enpass_notes_val)

                for i, cell_value_unstripped in enumerate(row_data):
                    cell_value = cell_value_unstripped.strip()
                    if i not in mapped_enpass_col_indices and cell_value:
                        original_field_name = enpass_header_stripped[i] if i < len(enpass_header_stripped) else f"Unnamed Field {i+1}"
                        additional_notes_list.append(f"{original_field_name}: {cell_value}")
                
                consolidated_notes = "\n".join(filter(None, additional_notes_list))

                csv_writer.writerow([
                    title_val,
                    url_val,
                    username_val,
                    password_val, # Keep original password spacing
                    consolidated_notes,
                    otpauth_url
                ])
                processed_rows += 1
            
            if processed_rows == 0 and row_num > 1: # Header was read but no data rows
                 print("Warning: CSV file contained a header but no data rows to process.")
            elif processed_rows > 0:
                print(f"Conversion successful. Processed {processed_rows} data rows.")
            else: # No header and no data rows (already caught, but for completeness)
                print("Warning: No data processed from the CSV file.")

            print(f"Output saved to '{output_filepath}'.")

    except FileNotFoundError:
        print(f"Fatal Error: Input file '{input_filepath}' not found.")
        raise
    except IOError as e:
        print(f"Fatal Error: Could not read from '{input_filepath}' or write to '{output_filepath}'. Details: {e}")
        raise
    except csv.Error as e: # Catches issues from csv.reader or if next() fails on empty reader
        print(f"Fatal Error: Problem parsing CSV data in '{input_filepath}'. Details: {e}")
        raise
    except Exception as e:
        print(f"An unexpected fatal error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise

def parse_enpass_json(input_filepath: str) -> list:
    """Parse Enpass JSON export and return a list of dicts with normalized fields."""
    with open(input_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items = data.get('items', [])
    result = []
    for item in items:
        entry = {}
        entry['Title'] = item.get('title', '')
        entry['Notes'] = item.get('note', '')
        # Map fields
        fields = item.get('fields', [])
        for field in fields:
            if field.get('deleted', 0):
                continue
            label = field.get('label', '').strip()
            value = field.get('value', '').strip()
            if not label or not value:
                continue
            # Try to map to Apple fields
            for apple_key, enpass_options in ENPASS_FIELD_MAPPINGS.items():
                if label in enpass_options:
                    entry[apple_key] = value
                    break
            # Always keep all fields for extra notes
            entry.setdefault('_extra', []).append(f"{label}: {value}")
        result.append(entry)
    return result


def write_apple_csv_from_dicts(dicts: list, output_filepath: str):
    """Write list of entry dicts to an Apple CSV file."""
    with open(output_filepath, 'w', newline='', encoding='utf-8') as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(APPLE_CSV_HEADER)
        for entry in dicts:
            title = entry.get('Title', '')
            url = entry.get('URL', '')
            username = entry.get('Username', '')
            password = entry.get('Password', '')
            totp = entry.get('TOTP', '')
            notes = entry.get('Notes', '')
            otpauth_url = generate_otpauth_url(totp, title, username)
            extra_notes = '\n'.join(entry.get('_extra', []))
            consolidated_notes = '\n'.join(filter(None, [notes, extra_notes]))
            csv_writer.writerow([
                title, url, username, password, consolidated_notes, otpauth_url
            ])


def transform_enpass_to_apple(input_filepath: str, output_filepath: str):
    """Detects file type (csv or json) and converts to Apple Passwords CSV."""
    if input_filepath.lower().endswith('.json'):
        dicts = parse_enpass_json(input_filepath)
        write_apple_csv_from_dicts(dicts, output_filepath)
    else:
        transform_enpass_csv_to_apple(input_filepath, output_filepath)


def main(
    enpass_input_file: str = typer.Argument(
        None, help="Path to your Enpass export CSV or JSON file.", show_default=False
    ),
    apple_output_file: str = typer.Argument(
        None, help="Desired output file path for Apple Passwords import.", show_default=False
    ),
):
    """Convert Enpass CSV or JSON export to Apple Passwords compatible CSV."""
    if not enpass_input_file:
        enpass_input_file = "export-enpass.csv"
        typer.secho(f"No input file specified. Using default: {enpass_input_file}", fg=typer.colors.YELLOW)
    if not apple_output_file:
        apple_output_file = "export-apple-passwords.csv"
        typer.secho(f"No output file specified. Using default: {apple_output_file}", fg=typer.colors.YELLOW)
    try:
        transform_enpass_to_apple(enpass_input_file, apple_output_file)
    except Exception as e:
        typer.secho(f"Script failed with an error. See details above. {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

app = typer.Typer()

@app.callback(invoke_without_command=True)
def cli(
    enpass_input_file: str = typer.Argument(
        None, help="Path to your Enpass export CSV or JSON file.", show_default=False
    ),
    apple_output_file: str = typer.Argument(
        None, help="Desired output file path for Apple Passwords import.", show_default=False
    ),
):
    """Convert Enpass CSV or JSON export to Apple Passwords compatible CSV."""
    main(enpass_input_file, apple_output_file)

if __name__ == "__main__":
    app()