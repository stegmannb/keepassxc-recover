"""Progress tracking and persistence for KeePassXC recovery."""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .credentials import Credential


@dataclass 
class ProgressData:
    """Progress data structure."""
    database_file: str
    database_hash: str
    started_at: str
    last_updated: str
    total_combinations: int
    attempts_made: int
    tried_combinations: List[Dict[str, Any]]
    current_index: int
    success: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgressData':
        """Create from dictionary."""
        return cls(**data)


class ProgressManager:
    """Manages recovery progress persistence."""
    
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self._progress: Optional[ProgressData] = None
    
    def calculate_database_hash(self, database_path: Path) -> str:
        """Calculate SHA256 hash of the database file."""
        sha256_hash = hashlib.sha256()
        with open(database_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def load_progress(self, database_path: Path) -> bool:
        """Load existing progress. Returns True if valid progress found."""
        if not self.progress_file.exists():
            return False
        
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
            
            self._progress = ProgressData.from_dict(data)
            
            # Validate database hasn't changed
            current_hash = self.calculate_database_hash(database_path)
            if self._progress.database_hash != current_hash:
                print(f"⚠️  Database file has changed (hash mismatch)")
                print(f"   Previous: {self._progress.database_hash}")
                print(f"   Current:  {current_hash}")
                print("   Starting fresh recovery...")
                self._progress = None
                return False
            
            # Validate database path matches
            if self._progress.database_file != str(database_path):
                print(f"⚠️  Database path mismatch")
                print(f"   Previous: {self._progress.database_file}")
                print(f"   Current:  {database_path}")
                print("   Starting fresh recovery...")
                self._progress = None
                return False
            
            return True
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"⚠️  Invalid progress file: {e}")
            print("   Starting fresh recovery...")
            self._progress = None
            return False
    
    def create_new_progress(self, database_path: Path, total_combinations: int) -> None:
        """Create new progress tracking."""
        now = datetime.now(timezone.utc).isoformat()
        database_hash = self.calculate_database_hash(database_path)
        
        self._progress = ProgressData(
            database_file=str(database_path),
            database_hash=database_hash,
            started_at=now,
            last_updated=now,
            total_combinations=total_combinations,
            attempts_made=0,
            tried_combinations=[],
            current_index=0
        )
        
        self._save_progress()
    
    def is_combination_tried(self, credential: Credential) -> bool:
        """Check if a combination has already been tried."""
        if not self._progress:
            return False
        
        credential_dict = credential.to_dict()
        return credential_dict in self._progress.tried_combinations
    
    def mark_combination_tried(self, credential: Credential) -> None:
        """Mark a combination as tried."""
        if not self._progress:
            return
        
        credential_dict = credential.to_dict()
        if credential_dict not in self._progress.tried_combinations:
            self._progress.tried_combinations.append(credential_dict)
            self._progress.attempts_made += 1
            self._progress.current_index += 1
            self._progress.last_updated = datetime.now(timezone.utc).isoformat()
            
            # Save progress every 10 attempts to avoid too frequent I/O
            if self._progress.attempts_made % 10 == 0:
                self._save_progress()
    
    def mark_success(self, credential: Credential) -> None:
        """Mark recovery as successful with the winning combination."""
        if not self._progress:
            return
        
        self._progress.success = credential.to_dict()
        self._progress.last_updated = datetime.now(timezone.utc).isoformat()
        self._save_progress()
    
    def get_progress_info(self) -> Optional[Dict[str, Any]]:
        """Get current progress information."""
        if not self._progress:
            return None
        
        return {
            'attempts_made': self._progress.attempts_made,
            'total_combinations': self._progress.total_combinations,
            'progress_percent': (self._progress.attempts_made / max(self._progress.total_combinations, 1)) * 100,
            'started_at': self._progress.started_at,
            'last_updated': self._progress.last_updated,
            'database_hash': self._progress.database_hash,
            'success': self._progress.success
        }
    
    def get_skip_count(self) -> int:
        """Get number of combinations to skip (already tried)."""
        if not self._progress:
            return 0
        return self._progress.attempts_made
    
    def _save_progress(self) -> None:
        """Save progress to file."""
        if not self._progress:
            return
        
        # Create backup of existing progress file
        if self.progress_file.exists():
            backup_file = self.progress_file.with_suffix('.json.backup')
            try:
                self.progress_file.rename(backup_file)
            except Exception:
                pass  # Ignore backup errors
        
        # Write new progress
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self._progress.to_dict(), f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save progress: {e}")
    
    def cleanup_progress(self) -> None:
        """Clean up progress file after successful recovery."""
        if self.progress_file.exists():
            try:
                # Keep a success record
                success_file = self.progress_file.with_suffix('.success.json')
                if self._progress and self._progress.success:
                    with open(success_file, 'w') as f:
                        json.dump({
                            'database_file': self._progress.database_file,
                            'database_hash': self._progress.database_hash,
                            'success_credential': self._progress.success,
                            'completed_at': datetime.now(timezone.utc).isoformat(),
                            'total_attempts': self._progress.attempts_made
                        }, f, indent=2)
                
                # Remove progress file
                self.progress_file.unlink()
                
                # Remove backup if exists
                backup_file = self.progress_file.with_suffix('.json.backup')
                if backup_file.exists():
                    backup_file.unlink()
                    
            except Exception as e:
                print(f"⚠️  Failed to cleanup progress files: {e}")