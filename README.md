# Enpass to Apple Password Migrator

A lightweight Python utility to convert Enpass CSV exports to Apple Password CSV import format. This tool helps users migrate their passwords from Enpass to Apple's password management system while preserving all critical information including TOTP/2FA secrets.

## 🚀 Features

- Converts Enpass CSV export format to Apple Password compatible format
- Preserves TOTP/2FA secrets with proper otpauth URI formatting
- Maintains credential information including titles, URLs, usernames, and passwords
- Combines additional fields into organized notes
- Zero external dependencies - pure Python implementation

## 📋 Prerequisites

- Python 3.6 or higher

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/ake2l/enpass-apple-migrator.git

# Navigate to the directory
cd Enpass-Apple-Migrator
```

## 💻 Usage

1. Export your passwords from Enpass as CSV
2. Place the exported CSV file as `input.csv` in the same directory as the script
3. Run the script:
```bash
python enpass_to_apple.py
```
4. Find the converted file as `output.csv`
5. Import the resulting CSV file into Apple Passwords

### Input Format (Enpass Export)
```csv
"Title","Username","value","E-Mail","value","*Password","value","Url","value","ADDITIONAL DETAILS","value"...
```

### Output Format (Apple Password Import)
```csv
Title,URL,Username,Password,Notes,OTPAuth
example,https://example.com,user@email.com,password123,additional notes,otpauth://totp/...
```

## 🔒 Security Considerations

- All processing is done locally on your machine
- No network connections are made
- No data is stored or cached
- Memory is cleared after processing
- No external dependencies required

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
