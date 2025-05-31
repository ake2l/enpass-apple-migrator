# Enpass-Escape

A lightweight Python CLI to migrate passwords from Enpass to Apple Passwords format. Supports both CSV and JSON exports, preserves TOTP/2FA secrets, and consolidates extra fields into notes.

## 🚀 Features

- Converts Enpass CSV or JSON export to Apple Passwords import CSV
- Preserves TOTP/2FA secrets with proper otpauth URI formatting
- Maintains titles, URLs, usernames, passwords, and notes
- Combines any additional fields into organized notes
- Zero external dependencies except Typer for the CLI interface

## 📋 Prerequisites

- Python 3.11 or higher

## 🛠️ Installation

Install from PyPI:

```bash
pip install enpass-escape
```

Or install development version:

```bash
git clone https://github.com/ake2l/enpass-apple-migrator.git
cd enpass-apple-migrator
pip install -e .
```

## 💻 Usage

Run the `enpass-escape` command with your Enpass export and desired output path:

```bash
# CSV-to-CSV
enpass-escape enpass-export.csv export-apple-passwords.csv

# JSON-to-CSV
enpass-escape export.json apple-output.csv

# View help
enpass-escape --help
```

The output CSV will have the header:

```csv
Title,URL,Username,Password,OTPAuth URL,Notes
```

### Input Formats

- **CSV**: Standard Enpass CSV export
- **JSON**: Enpass JSON export

### Output Format

Apple Passwords import CSV with the following columns:

```csv
Title,URL,Username,Password,OTPAuth URL,Notes
```

## 🔒 Security Considerations

- All processing is local; no network calls
- No data is stored or cached
- No external dependencies other than Typer

## 🤝 Contributing

Contributions welcome! Open an issue or submit a pull request.

## 📝 License

MIT License. See [LICENSE](LICENSE) for details.