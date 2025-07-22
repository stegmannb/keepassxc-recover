#!/usr/bin/env python3
"""KeePassXC Database Recovery Tool CLI."""

import click
import sys
from pathlib import Path
from typing import List, Optional

from .recovery import RecoveryEngine
from .credentials import CredentialManager
from .progress import ProgressManager


@click.command()
@click.argument('database', type=click.Path(exists=True, path_type=Path))
@click.option('--passphrases', '-p', type=click.Path(exists=True, path_type=Path), 
              help='File containing passphrases (one per line)')
@click.option('--passphrases-list', multiple=True, 
              help='Individual passphrases (can be used multiple times)')
@click.option('--keyfiles', '-k', type=click.Path(exists=True, path_type=Path), 
              help='Directory containing keyfiles')
@click.option('--keyfile-list', multiple=True, type=click.Path(exists=True, path_type=Path),
              help='Individual keyfiles (can be used multiple times)')
@click.option('--yubikey/--no-yubikey', default=False, 
              help='Try with/without YubiKey')
@click.option('--yubikey-slots', default='1,2', 
              help='YubiKey slots to try (comma-separated, default: 1,2)')
@click.option('--try-no-password/--skip-no-password', default=True,
              help='Try combinations without passphrase (default: enabled)')
@click.option('--try-no-keyfile/--skip-no-keyfile', default=True, 
              help='Try combinations without keyfiles (default: enabled)')
@click.option('--progress-file', type=click.Path(path_type=Path),
              default='.recovery_progress.json',
              help='Progress file location (default: .recovery_progress.json)')
@click.option('--resume/--no-resume', default=True,
              help='Resume from previous progress (default: True)')
@click.option('--timeout', type=int, default=30,
              help='Timeout per attempt in seconds (default: 30)')
@click.option('--quiet', '-q', is_flag=True,
              help='Suppress output except for success/failure')
def main(
    database: Path,
    passphrases: Optional[Path],
    passphrases_list: tuple,
    keyfiles: Optional[Path],
    keyfile_list: tuple,
    yubikey: bool,
    yubikey_slots: str,
    try_no_password: bool,
    try_no_keyfile: bool,
    progress_file: Path,
    resume: bool,
    timeout: int,
    quiet: bool
):
    """Recover KeePassXC database by trying multiple credential combinations.
    
    DATABASE: Path to the KeePassXC database file (.kdbx)
    """
    
    # Validate inputs - allow no passphrases if other credentials provided
    has_passphrases = passphrases or passphrases_list
    has_keyfiles = keyfiles or keyfile_list
    has_yubikey = yubikey
    
    if not has_passphrases and not has_keyfiles and not has_yubikey:
        click.echo("Error: Must provide at least one credential type (passphrases, keyfiles, or yubikey)", err=True)
        sys.exit(1)
    
    # Initialize components
    try:
        # Load credentials
        credential_manager = CredentialManager()
        
        if passphrases:
            credential_manager.load_passphrases_from_file(passphrases)
        
        if passphrases_list:
            credential_manager.add_passphrases(list(passphrases_list))
            
        if keyfiles:
            credential_manager.load_keyfiles_from_directory(keyfiles)
            
        if keyfile_list:
            credential_manager.add_keyfiles(list(keyfile_list))
            
        if yubikey:
            slots = [int(s.strip()) for s in yubikey_slots.split(',')]
            credential_manager.set_yubikey_slots(slots)
        
        # Enable no-password and no-keyfile options (enabled by default)
        credential_manager.enable_no_passphrase(try_no_password)
        credential_manager.enable_no_keyfile(try_no_keyfile)
        
        # Initialize progress manager
        progress_manager = ProgressManager(progress_file)
        
        # Initialize recovery engine
        recovery_engine = RecoveryEngine(
            database=database,
            credential_manager=credential_manager,
            progress_manager=progress_manager,
            timeout=timeout,
            quiet=quiet
        )
        
        # Start recovery
        success = recovery_engine.run(resume=resume)
        
        if success:
            click.echo("✅ Database unlocked successfully!")
            sys.exit(0)
        else:
            click.echo("❌ Failed to unlock database with any combination")
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo("\n⏸️  Recovery interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"💥 Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()