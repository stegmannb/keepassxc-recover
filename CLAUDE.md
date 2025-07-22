# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a KeePassXC database recovery tool written in Python. It systematically tries multiple credential combinations (passphrases, keyfiles, YubiKey) to recover access to locked KeePassXC databases. The project uses modern Python development tools with Mise for tool management and UV for dependency management.

## Main Tool Usage

### Basic Recovery Commands
- `recover database.kdbx --passphrases passphrases.txt` - Try passphrases from file
- `recover database.kdbx --keyfiles keyfiles/` - Try keyfiles from directory
- `recover database.kdbx --yubikey` - Try YubiKey combinations
- `recover database.kdbx --passphrases passphrases.txt --keyfiles keyfiles/ --yubikey` - Comprehensive recovery

### Key Features
- **Resumable**: Progress saved to `.recovery_progress.json`, can be interrupted and resumed
- **Database integrity**: SHA256 hash validation prevents running on changed databases
- **Comprehensive**: By default tries all combinations including no-password/no-keyfile scenarios
- **YubiKey support**: Uses `keepassxc-cli` for full YubiKey hardware key support

## Development Commands

### Environment Setup
- `mise sync` - Install and sync all dependencies (Python, UV, and project dependencies)
- `uv sync` - Sync Python dependencies directly

### Code Formatting
- `mise run format` - Format all files (runs prettier and shfmt)
- `mise run format:prettier` - Format files with Prettier
- `mise run format:shfmt` - Format shell scripts with shfmt

### Testing
- Test with sample database: `recover api.kdbx --passphrases passphrases.txt --keyfiles keyfiles/`
- The tool uses `keepassxc-cli` internally, ensure it's available: `which keepassxc-cli`

## Project Architecture

### Core Components
- `recover/cli.py` - Command-line interface using Click
- `recover/credentials.py` - Credential management and combination generation
- `recover/progress.py` - Progress tracking with database hash validation
- `recover/recovery.py` - Core recovery engine using keepassxc-cli subprocess calls

### Key Design Decisions
- Uses `keepassxc-cli` subprocess calls instead of pykeepass for full YubiKey support
- Generates all credential combinations via itertools.product()
- Progress persistence prevents losing work on interruption
- Database hash validation prevents running on wrong/changed files

## Project Configuration

### Python Environment
- Python version: 3.13.2 (managed by Mise)
- Virtual environment: `.venv` (auto-created by Mise)
- Dependencies: click, tqdm (minimal dependencies for CLI tool)
- Project requires Python >=3.13

### Tool Management
- Mise manages Python and UV versions
- UV handles Python package dependencies
- Entry point: `recover` command available after `uv sync`

## Development Workflow

1. Run `mise sync` to set up the development environment
2. Use `mise run format` before committing changes
3. Test changes with sample databases in the repo
4. The tool is defensive security focused - for recovering your own databases only