# KeePassXC Database Recovery Tool

A Python CLI tool to recover access to KeePassXC databases by trying multiple credential combinations systematically.

## Features

- **Multiple authentication factors**: Supports passphrases, keyfiles, and YubiKey hardware keys
- **Resumable recovery**: Saves progress and can be interrupted and resumed later
- **Database integrity checking**: Validates database hasn't changed between runs using SHA256 hash
- **Progress tracking**: Shows real-time progress with estimated completion time
- **Flexible input**: Load credentials from files or command line arguments

## Installation

```bash
# Set up development environment
mise sync

# The tool will be available as `recover` command
```

## Usage

### Basic Examples

```bash
# Try passphrases from a file
recover database.kdbx --passphrases passphrases.txt

# Try specific passphrases from command line
recover database.kdbx --passphrases-list "password1" --passphrases-list "password2"

# Try passphrases with keyfiles from directory
recover database.kdbx --passphrases passphrases.txt --keyfiles ./keyfiles/

# Try specific keyfile
recover database.kdbx --passphrases passphrases.txt --keyfile-list ./my.key

# Try with YubiKey (requires YubiKey to be present)
recover database.kdbx --passphrases passphrases.txt --yubikey --yubikey-slots 1,2

# Try keyfile-only combinations (no password) - enabled by default
recover database.kdbx --keyfiles ./keyfiles/

# Try YubiKey-only combinations (no password, no keyfile) - enabled by default  
recover database.kdbx --yubikey

# Try all possible combinations (default behavior)
recover database.kdbx \\
  --passphrases passphrases.txt \\
  --keyfiles ./keyfiles/ \\
  --yubikey \\
  --yubikey-slots 1,2
```

### Advanced Options

```bash
# Custom progress file location
recover database.kdbx --passphrases passphrases.txt --progress-file custom_progress.json

# Start fresh (don't resume from previous run)
recover database.kdbx --passphrases passphrases.txt --no-resume

# Increase timeout for slow systems
recover database.kdbx --passphrases passphrases.txt --timeout 60

# Quiet mode (minimal output)
recover database.kdbx --passphrases passphrases.txt --quiet

# Skip no-password combinations (if you're sure password is required)
recover database.kdbx --passphrases passphrases.txt --skip-no-password

# Skip no-keyfile combinations (if you're sure keyfile is required)  
recover database.kdbx --passphrases passphrases.txt --keyfiles ./keyfiles/ --skip-no-keyfile
```

## File Formats

### Passphrase File Format
```
# Comments start with #
password123
my secret passphrase
another-password
# Empty lines are ignored

final_password
```

### Progress File
The tool automatically creates a `.recovery_progress.json` file that contains:
- Database file path and SHA256 hash
- List of attempted combinations  
- Current progress and timing information
- Success status and winning combination

## How It Works

1. **Load credentials** from files/arguments
2. **Generate combinations** of all possible credential factors
3. **Check for existing progress** and validate database integrity
4. **Test each combination** using `keepassxc-cli` 
5. **Save progress** regularly to enable resumption
6. **Report success** and clean up when database is unlocked

## Security Notes

- This tool is designed for recovering **your own** databases
- Passphrases are passed securely to `keepassxc-cli` via stdin
- Progress files contain attempted combinations - keep them secure
- Original database file is never modified (read-only operations)

## Requirements

- Python 3.13+
- KeePassXC with `keepassxc-cli` command available
- YubiKey support requires YubiKey with HMAC-SHA1 Challenge-Response configured

## Development

```bash
# Set up environment
mise sync

# Run formatting
mise run format

# Install in development mode
uv sync
```