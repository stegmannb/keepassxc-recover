# KeePassXC Database Recovery Tool

A Python CLI tool to recover access to KeePassXC databases by systematically trying multiple credential combinations.

## Features

- **Multiple authentication factors**: Supports passphrases, keyfiles, and YubiKey hardware keys
- **Resumable recovery**: Saves progress and can be interrupted and resumed later
- **Database integrity checking**: Validates database hasn't changed between runs using SHA256 hash
- **Progress tracking**: Shows real-time progress with estimated completion time
- **Flexible input**: Load credentials from files or command line arguments

## Installation

### Prerequisites

- [Mise](https://mise.jdx.dev/) (for tool management)
- KeePassXC with `keepassxc-cli` command available in PATH
- YubiKey (optional, for hardware key support)

### Setup

```bash
# Clone the repository
git clone https://github.com/stegmannb/keepassxc-recover.git
cd recover

# Set up development environment with Mise
mise install
mise run sync

# The tool will be available as `keepassxc-recover` command after sync
```

### Alternative Installation Methods

**Direct installation with UV:**

```bash
# Install directly from GitHub
uv tool install git+https://github.com/stegmannb/keepassxc-recover.git

# Or install from PyPI (when published)
uv tool install recover
```

**Installation with pip:**

```bash
# Install directly from GitHub
pip install git+https://github.com/stegmannb/keepassxc-recover.git

# Or install from PyPI (when published)
pip install recover
```

### Verify Installation

```bash
# Check that the tool is available
keepassxc-recover --help

# Verify keepassxc-cli is available
which keepassxc-cli
```

## Usage

### Basic Examples

```bash
# Try passphrases from a file
keepassxc-recover database.kdbx --passphrases passphrases.txt

# Try specific passphrases from command line
keepassxc-recover database.kdbx --passphrases-list "password1" --passphrases-list "password2"

# Try passphrases with keyfiles from directory
keepassxc-recover database.kdbx --passphrases passphrases.txt --keyfiles ./keyfiles/

# Try specific keyfile
keepassxc-recover database.kdbx --passphrases passphrases.txt --keyfile-list ./my.key

# Try with YubiKey (requires YubiKey to be present)
keepassxc-recover database.kdbx --passphrases passphrases.txt --yubikey --yubikey-slots 1,2

# Try keyfile-only combinations (no password) - enabled by default
keepassxc-recover database.kdbx --keyfiles ./keyfiles/

# Try YubiKey-only combinations (no password, no keyfile) - enabled by default
keepassxc-recover database.kdbx --yubikey

# Try all possible combinations (default behavior)
keepassxc-recover database.kdbx \\
  --passphrases passphrases.txt \\
  --keyfiles ./keyfiles/ \\
  --yubikey \\
  --yubikey-slots 1,2
```

### Advanced Options

```bash
# Custom progress file location
keepassxc-recover database.kdbx --passphrases passphrases.txt --progress-file custom_progress.json

# Start fresh (don't resume from previous run)
keepassxc-recover database.kdbx --passphrases passphrases.txt --no-resume

# Increase timeout for slow systems
keepassxc-recover database.kdbx --passphrases passphrases.txt --timeout 60

# Quiet mode (minimal output)
keepassxc-recover database.kdbx --passphrases passphrases.txt --quiet

# Skip no-password combinations (if you're sure password is required)
keepassxc-recover database.kdbx --passphrases passphrases.txt --skip-no-password

# Skip no-keyfile combinations (if you're sure keyfile is required)
keepassxc-recover database.kdbx --passphrases passphrases.txt --keyfiles ./keyfiles/ --skip-no-keyfile
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

1. **Load credentials** from files/arguments (passphrases, keyfiles, YubiKey slots)
2. **Generate combinations** using itertools.product() for all possible credential combinations
3. **Check for existing progress** and validate database integrity via SHA256 hash
4. **Test each combination** using `keepassxc-cli` subprocess calls for full YubiKey support
5. **Save progress** regularly to `.recovery_progress.json` to enable interruption/resumption
6. **Report success** with winning combination and clean up when database is unlocked

### Recovery Process Details

The tool systematically tests combinations in this order:

- No password, no keyfile, no YubiKey (if enabled)
- Password only combinations
- Keyfile only combinations (if enabled)
- YubiKey only combinations (if enabled)
- Password + keyfile combinations
- Password + YubiKey combinations
- Keyfile + YubiKey combinations
- Password + keyfile + YubiKey combinations

This approach ensures simpler combinations are tried first before more complex ones.

## Security Notes

- This tool is designed for recovering **your own** databases
- Passphrases are passed securely to `keepassxc-cli` via stdin
- Progress files contain attempted combinations - keep them secure
- Original database file is never modified (read-only operations)

## Requirements

- Python 3.13+
- KeePassXC with `keepassxc-cli` command available
- YubiKey support requires YubiKey with HMAC-SHA1 Challenge-Response configured

## Project Structure

```
recover/
├── recover/              # Main package directory
│   ├── __init__.py      # Package initialization
│   ├── cli.py           # Command-line interface using Click
│   ├── credentials.py   # Credential management and combination generation
│   ├── progress.py      # Progress tracking with database hash validation
│   └── recovery.py      # Core recovery engine using keepassxc-cli
├── keyfiles/            # Sample keyfiles directory
├── passphrases.txt      # Sample passphrases file
├── *.kdbx              # Sample KeePassXC database files
├── mise.toml           # Mise tool configuration
├── pyproject.toml      # Python project configuration
└── CLAUDE.md           # AI assistant instructions
```

## Development

### Environment Setup

```bash
# Set up environment
mise sync

# Install dependencies directly with UV
uv sync
```

### Code Formatting

```bash
# Format all files (runs prettier and shfmt)
mise run format

# Format specific file types
mise run format:prettier  # Format files with Prettier
mise run format:shfmt     # Format shell scripts with shfmt
```

### Testing

```bash
# Test with sample database
keepassxc-recover api.kdbx --passphrases passphrases.txt --keyfiles keyfiles/

# Test YubiKey functionality (requires YubiKey)
keepassxc-recover api.kdbx --yubikey --yubikey-slots 1,2
```

## Troubleshooting

### Common Issues

**`keepassxc-cli` not found**

```bash
# On Ubuntu/Debian
sudo apt install keepassxc

# On macOS with Homebrew
brew install keepassxc

# Verify installation
which keepassxc-cli
```

**YubiKey not detected**

- Ensure YubiKey is properly inserted and detected by the system
- Verify YubiKey has HMAC-SHA1 Challenge-Response configured
- Test YubiKey with KeePassXC GUI first

**Progress file corruption**

- Delete `.recovery_progress.json` and restart with `--no-resume`
- Check if database file changed (different SHA256 hash)

**Memory or performance issues**

- For large credential sets, consider splitting passphrases into smaller files
- Increase `--timeout` for slower systems
- Use `--quiet` to reduce output overhead

### Getting Help

- Check command help: `keepassxc-recover --help`
- Review sample files in the repository for format examples
- Verify your credentials work manually with `keepassxc-cli` first

## License

This project is a defensive security tool intended for recovering access to your own KeePassXC databases only.
