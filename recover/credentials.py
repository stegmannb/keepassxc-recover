"""Credential management for KeePassXC recovery."""

import itertools
from pathlib import Path
from typing import List, Optional, Iterator, Dict, Any
from dataclasses import dataclass


@dataclass
class Credential:
    """Represents a credential combination."""
    passphrase: Optional[str] = None
    keyfile: Optional[Path] = None
    yubikey_slot: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'passphrase': self.passphrase,
            'keyfile': str(self.keyfile) if self.keyfile else None,
            'yubikey_slot': self.yubikey_slot
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Credential':
        """Create from dictionary."""
        return cls(
            passphrase=data.get('passphrase'),
            keyfile=Path(data['keyfile']) if data.get('keyfile') else None,
            yubikey_slot=data.get('yubikey_slot')
        )
    
    def __str__(self) -> str:
        """String representation for logging."""
        parts = []
        if self.passphrase:
            parts.append(f"passphrase='***'")
        if self.keyfile:
            parts.append(f"keyfile='{self.keyfile.name}'")
        if self.yubikey_slot:
            parts.append(f"yubikey_slot={self.yubikey_slot}")
        return f"Credential({', '.join(parts)})"


class CredentialManager:
    """Manages passphrases, keyfiles, and YubiKey options."""
    
    def __init__(self):
        self.passphrases: List[str] = []
        self.keyfiles: List[Path] = []
        self.yubikey_slots: List[int] = []
        self._include_no_passphrase = False
        self._include_no_keyfile = False
        self._include_no_yubikey = True  # Default to trying without YubiKey
    
    def load_passphrases_from_file(self, filepath: Path) -> None:
        """Load passphrases from a file (one per line)."""
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                passphrase = line.strip()
                if passphrase and not passphrase.startswith('#'):  # Skip empty lines and comments
                    self.passphrases.append(passphrase)
    
    def add_passphrases(self, passphrases: List[str]) -> None:
        """Add passphrases from a list."""
        self.passphrases.extend(passphrases)
    
    def load_keyfiles_from_directory(self, directory: Path) -> None:
        """Load all files from a directory as potential keyfiles."""
        if not directory.is_dir():
            raise ValueError(f"Directory does not exist: {directory}")
        
        for filepath in directory.iterdir():
            if filepath.is_file():
                self.keyfiles.append(filepath)
    
    def add_keyfiles(self, keyfiles: List[Path]) -> None:
        """Add keyfiles from a list."""
        self.keyfiles.extend(keyfiles)
    
    def set_yubikey_slots(self, slots: List[int]) -> None:
        """Set YubiKey slots to try."""
        self.yubikey_slots = slots
        # For recovery purposes, still try combinations without YubiKey
        # self._include_no_yubikey = False  # Keep trying without YubiKey for comprehensive recovery
    
    def enable_try_all_combinations(self) -> None:
        """Enable trying all possible combinations including no-password scenarios."""
        self._include_no_passphrase = True
        self._include_no_keyfile = True
        # Keep YubiKey setting as is - it's handled separately
    
    def enable_no_passphrase(self, enabled: bool = True) -> None:
        """Enable trying combinations without passphrase."""
        self._include_no_passphrase = enabled
    
    def enable_no_keyfile(self, enabled: bool = True) -> None:
        """Enable trying combinations without keyfile."""
        self._include_no_keyfile = enabled
    
    def generate_combinations(self) -> Iterator[Credential]:
        """Generate all possible credential combinations."""
        # Prepare passphrase options
        passphrase_options = self.passphrases.copy()
        if self._include_no_passphrase:
            passphrase_options.append(None)
        
        # If no passphrases provided but we have other factors, enable no-passphrase
        if not self.passphrases and (self.keyfiles or self.yubikey_slots):
            passphrase_options.append(None)
        
        # Prepare keyfile options  
        keyfile_options = self.keyfiles.copy()
        if self._include_no_keyfile or not self.keyfiles:
            keyfile_options.append(None)
        
        # Prepare YubiKey options
        yubikey_options = self.yubikey_slots.copy()
        if self._include_no_yubikey:
            yubikey_options.append(None)
        
        # Generate all combinations
        for passphrase, keyfile, yubikey_slot in itertools.product(
            passphrase_options, keyfile_options, yubikey_options
        ):
            # Skip invalid combinations - must have at least one credential factor
            if passphrase is None and keyfile is None and yubikey_slot is None:
                continue
                
            yield Credential(
                passphrase=passphrase,
                keyfile=keyfile,
                yubikey_slot=yubikey_slot
            )
    
    def count_combinations(self) -> int:
        """Count total number of combinations that would be generated."""
        return sum(1 for _ in self.generate_combinations())
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about loaded credentials."""
        return {
            'passphrases': len(self.passphrases),
            'keyfiles': len(self.keyfiles), 
            'yubikey_slots': len(self.yubikey_slots),
            'total_combinations': self.count_combinations()
        }