# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "recover" configured with modern Python development tools using Mise for tool management and UV for dependency management.

## Development Commands

### Environment Setup
- `mise sync` - Install and sync all dependencies (Python, UV, and project dependencies)
- `mise tasks sync:mise` - Sync Mise-managed tools (Python, UV)
- `mise tasks sync:uv` - Sync Python dependencies via UV

### Code Formatting
- `mise run format` - Format all files (runs prettier and shfmt)
- `mise run format:prettier` - Format files with Prettier
- `mise run format:shfmt` - Format shell scripts with shfmt

## Project Configuration

### Python Environment
- Python version: 3.12.6 (managed by Mise)
- Virtual environment: `.venv` (auto-created by Mise)
- Dependencies managed by UV
- Project requires Python >=3.13 (as per pyproject.toml)

### Tool Management
- Mise manages Python and UV versions
- UV handles Python package dependencies
- Project uses env.yaml for additional environment configuration

## Development Workflow

1. Run `mise sync` to set up the development environment
2. Use `mise run format` before committing changes
3. The project uses UV for fast Python dependency management within a Mise-managed environment