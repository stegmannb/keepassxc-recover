"""Core recovery engine for KeePassXC database recovery."""

import subprocess
import sys
import signal
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm

from .credentials import Credential, CredentialManager
from .progress import ProgressManager


class RecoveryEngine:
    """Main recovery engine that orchestrates the recovery process."""
    
    def __init__(
        self,
        database: Path,
        credential_manager: CredentialManager,
        progress_manager: ProgressManager,
        timeout: int = 30,
        quiet: bool = False
    ):
        self.database = database
        self.credential_manager = credential_manager
        self.progress_manager = progress_manager
        self.timeout = timeout
        self.quiet = quiet
        self._interrupted = False
        
        # Set up signal handling for graceful interruption
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interruption signals gracefully."""
        self._interrupted = True
        if not self.quiet:
            print("\n⏸️  Stopping recovery, saving progress...")
    
    def _build_keepassxc_command(self, credential: Credential) -> List[str]:
        """Build keepassxc-cli command for a given credential combination."""
        cmd = ['keepassxc-cli', 'open', '--quiet']
        
        # Add keyfile if specified
        if credential.keyfile:
            cmd.extend(['--key-file', str(credential.keyfile)])
        
        # Add YubiKey if specified
        if credential.yubikey_slot:
            cmd.extend(['--yubikey', str(credential.yubikey_slot)])
        
        # Add no-password flag if no passphrase
        if credential.passphrase is None:
            cmd.append('--no-password')
        
        # Add database path
        cmd.append(str(self.database))
        
        return cmd
    
    def _test_credential(self, credential: Credential) -> bool:
        """Test a single credential combination."""
        try:
            cmd = self._build_keepassxc_command(credential)
            
            # Prepare input (passphrase if needed)
            input_data = None
            if credential.passphrase is not None:
                input_data = credential.passphrase.encode('utf-8') + b'\n'
            
            # Run keepassxc-cli
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                timeout=self.timeout,
                text=False  # Use bytes for input
            )
            
            # Success if exit code is 0
            success = result.returncode == 0
            
            if success and not self.quiet:
                print(f"\n✅ SUCCESS with {credential}")
                if result.stdout:
                    print("Database contents preview:")
                    print(result.stdout.decode('utf-8', errors='replace'))
            
            return success
            
        except subprocess.TimeoutExpired:
            if not self.quiet:
                print(f"⏱️  Timeout testing {credential}")
            return False
        except subprocess.SubprocessError as e:
            if not self.quiet:
                print(f"❌ Error testing {credential}: {e}")
            return False
        except Exception as e:
            if not self.quiet:
                print(f"💥 Unexpected error testing {credential}: {e}")
            return False
    
    def run(self, resume: bool = True) -> bool:
        """Run the recovery process."""
        
        # Load or create progress
        progress_loaded = False
        if resume:
            progress_loaded = self.progress_manager.load_progress(self.database)
        
        if progress_loaded:
            progress_info = self.progress_manager.get_progress_info()
            if not self.quiet:
                print(f"📂 Resuming recovery from previous session")
                print(f"   Database: {self.database}")
                print(f"   Started: {progress_info['started_at']}")
                print(f"   Attempts made: {progress_info['attempts_made']}")
                print(f"   Progress: {progress_info['progress_percent']:.1f}%")
                print()
        else:
            total_combinations = self.credential_manager.count_combinations()
            self.progress_manager.create_new_progress(self.database, total_combinations)
            
            if not self.quiet:
                stats = self.credential_manager.get_stats()
                print(f"🔐 Starting KeePassXC database recovery")
                print(f"   Database: {self.database}")
                print(f"   Passphrases: {stats['passphrases']}")
                print(f"   Keyfiles: {stats['keyfiles']}")
                print(f"   YubiKey slots: {stats['yubikey_slots']}")
                print(f"   Total combinations: {stats['total_combinations']}")
                print()
                
        
        # Get total combinations and skip count
        progress_info = self.progress_manager.get_progress_info()
        total_combinations = progress_info['total_combinations']
        skip_count = self.progress_manager.get_skip_count()
        
        # Set up progress bar
        progress_bar = None
        if not self.quiet:
            progress_bar = tqdm(
                total=total_combinations,
                initial=skip_count,
                desc="Testing combinations",
                unit="combo",
                ncols=100
            )
        
        try:
            # Test each combination
            combination_index = 0
            for credential in self.credential_manager.generate_combinations():
                
                # Check for interruption
                if self._interrupted:
                    break
                
                # Skip already tried combinations
                if combination_index < skip_count:
                    combination_index += 1
                    continue
                
                # Skip if already tried (additional safety check)
                if self.progress_manager.is_combination_tried(credential):
                    combination_index += 1
                    if progress_bar:
                        progress_bar.update(1)
                    continue
                
                # Test the combination
                if not self.quiet:
                    progress_bar.set_postfix_str(f"Testing: {credential}")
                
                success = self._test_credential(credential)
                
                # Mark as tried
                self.progress_manager.mark_combination_tried(credential)
                combination_index += 1
                
                if progress_bar:
                    progress_bar.update(1)
                
                if success:
                    # Found the right combination!
                    self.progress_manager.mark_success(credential)
                    if progress_bar:
                        progress_bar.close()
                    
                    if not self.quiet:
                        print(f"\n🎉 Database successfully unlocked!")
                        print(f"   Winning combination: {credential}")
                        print(f"   Attempts required: {combination_index}")
                    
                    # Clean up progress file
                    self.progress_manager.cleanup_progress()
                    return True
            
            # If we get here, no combination worked
            if progress_bar:
                progress_bar.close()
                
            if not self.quiet:
                if self._interrupted:
                    print(f"\n⏸️  Recovery interrupted after {combination_index} attempts")
                    print("   Progress saved. Run again with --resume to continue.")
                else:
                    print(f"\n❌ Recovery failed - no working combination found")
                    print(f"   Total attempts: {combination_index}")
            
            return False
            
        except Exception as e:
            if progress_bar:
                progress_bar.close()
            if not self.quiet:
                print(f"\n💥 Recovery failed with error: {e}")
            return False
        finally:
            # Always save final progress
            if progress_bar:
                progress_bar.close()