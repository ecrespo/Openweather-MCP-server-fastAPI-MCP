"""
Token Repository Implementations.

This module provides concrete implementations of the TokenRepository protocol,
offering different strategies for token storage and retrieval.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import threading
import json
import os
from pathlib import Path

from utils.logger import log


class InMemoryTokenRepository:
    """
    In-memory token repository.

    This implementation stores tokens in memory, suitable for development,
    testing, or single-process deployments. Data is lost on restart.

    Implements the TokenRepository protocol.

    :ivar tokens: Dictionary storing token data
    :ivar lock: Thread lock for token operations
    """

    def __init__(self):
        """Initialize the in-memory token repository."""
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        log.info("InMemoryTokenRepository initialized")

    def get(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves token information by token ID.

        Args:
            token_id: Unique identifier for the token

        Returns:
            Dictionary containing token information if found, None otherwise
        """
        with self.lock:
            token_data = self.tokens.get(token_id)
            if token_data:
                # Check if token is expired
                if 'expires_at' in token_data:
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at < datetime.now():
                        log.debug(f"Token {token_id} has expired")
                        return None
            return token_data

    def save(self, token_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Saves token information to memory.

        Args:
            token_id: Unique identifier for the token
            token_data: Dictionary containing token information

        Returns:
            True if saved successfully
        """
        try:
            with self.lock:
                # Add timestamp if not present
                if 'created_at' not in token_data:
                    token_data['created_at'] = datetime.now().isoformat()

                self.tokens[token_id] = token_data
                log.debug(f"Token {token_id} saved successfully")
                return True
        except Exception as e:
            log.error(f"Error saving token {token_id}: {e}")
            return False

    def delete(self, token_id: str) -> bool:
        """
        Deletes a token from memory.

        Args:
            token_id: Unique identifier for the token

        Returns:
            True if deleted successfully, False if token not found
        """
        with self.lock:
            if token_id in self.tokens:
                del self.tokens[token_id]
                log.debug(f"Token {token_id} deleted")
                return True
            return False

    def exists(self, token_id: str) -> bool:
        """
        Checks if a token exists in memory.

        Args:
            token_id: Unique identifier for the token

        Returns:
            True if token exists and is not expired
        """
        return self.get(token_id) is not None

    def get_all_active(self) -> List[Dict[str, Any]]:
        """
        Retrieves all active (non-expired) tokens.

        Returns:
            List of token information dictionaries
        """
        with self.lock:
            active_tokens = []
            now = datetime.now()

            for token_id, token_data in self.tokens.items():
                # Check expiration
                if 'expires_at' in token_data:
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at < now:
                        continue

                active_tokens.append({
                    'token_id': token_id,
                    **token_data
                })

            return active_tokens

    def cleanup_expired(self) -> int:
        """
        Removes expired tokens from memory.

        Returns:
            Number of expired tokens removed
        """
        with self.lock:
            now = datetime.now()
            expired_tokens = []

            for token_id, token_data in self.tokens.items():
                if 'expires_at' in token_data:
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at < now:
                        expired_tokens.append(token_id)

            for token_id in expired_tokens:
                del self.tokens[token_id]

            if expired_tokens:
                log.info(f"Cleaned up {len(expired_tokens)} expired tokens")

            return len(expired_tokens)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the token repository.

        Returns:
            Dictionary with repository statistics
        """
        with self.lock:
            active = len(self.get_all_active())
            total = len(self.tokens)

            return {
                'total_tokens': total,
                'active_tokens': active,
                'expired_tokens': total - active
            }


class FileTokenRepository:
    """
    File-based token repository.

    This implementation persists tokens to a JSON file, providing persistence
    across restarts while maintaining simplicity.

    Implements the TokenRepository protocol.

    :ivar file_path: Path to the token storage file
    :ivar tokens: Dictionary storing token data (cached in memory)
    :ivar lock: Thread lock for file operations
    """

    def __init__(self, file_path: str = "./data/tokens.json"):
        """
        Initialize the file-based token repository.

        Args:
            file_path: Path to the JSON file for token storage
        """
        self.file_path = Path(file_path)
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

        # Create directory if it doesn't exist
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing tokens
        self._load_from_file()
        log.info(f"FileTokenRepository initialized with file: {self.file_path}")

    def _load_from_file(self) -> None:
        """Load tokens from the JSON file."""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    self.tokens = json.load(f)
                log.debug(f"Loaded {len(self.tokens)} tokens from file")
            else:
                self.tokens = {}
                log.debug("No existing token file found, starting with empty storage")
        except Exception as e:
            log.error(f"Error loading tokens from file: {e}")
            self.tokens = {}

    def _save_to_file(self) -> bool:
        """Save tokens to the JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.tokens, f, indent=2)
            log.debug(f"Saved {len(self.tokens)} tokens to file")
            return True
        except Exception as e:
            log.error(f"Error saving tokens to file: {e}")
            return False

    def get(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves token information by token ID.

        Args:
            token_id: Unique identifier for the token

        Returns:
            Dictionary containing token information if found, None otherwise
        """
        with self.lock:
            token_data = self.tokens.get(token_id)
            if token_data:
                # Check if token is expired
                if 'expires_at' in token_data:
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at < datetime.now():
                        log.debug(f"Token {token_id} has expired")
                        return None
            return token_data

    def save(self, token_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Saves token information to file.

        Args:
            token_id: Unique identifier for the token
            token_data: Dictionary containing token information

        Returns:
            True if saved successfully
        """
        try:
            with self.lock:
                # Add timestamp if not present
                if 'created_at' not in token_data:
                    token_data['created_at'] = datetime.now().isoformat()

                self.tokens[token_id] = token_data
                success = self._save_to_file()

                if success:
                    log.debug(f"Token {token_id} saved successfully to file")
                return success
        except Exception as e:
            log.error(f"Error saving token {token_id}: {e}")
            return False

    def delete(self, token_id: str) -> bool:
        """
        Deletes a token from file storage.

        Args:
            token_id: Unique identifier for the token

        Returns:
            True if deleted successfully, False if token not found
        """
        with self.lock:
            if token_id in self.tokens:
                del self.tokens[token_id]
                self._save_to_file()
                log.debug(f"Token {token_id} deleted from file")
                return True
            return False

    def exists(self, token_id: str) -> bool:
        """
        Checks if a token exists in storage.

        Args:
            token_id: Unique identifier for the token

        Returns:
            True if token exists and is not expired
        """
        return self.get(token_id) is not None

    def get_all_active(self) -> List[Dict[str, Any]]:
        """
        Retrieves all active (non-expired) tokens.

        Returns:
            List of token information dictionaries
        """
        with self.lock:
            active_tokens = []
            now = datetime.now()

            for token_id, token_data in self.tokens.items():
                # Check expiration
                if 'expires_at' in token_data:
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at < now:
                        continue

                active_tokens.append({
                    'token_id': token_id,
                    **token_data
                })

            return active_tokens

    def cleanup_expired(self) -> int:
        """
        Removes expired tokens from file storage.

        Returns:
            Number of expired tokens removed
        """
        with self.lock:
            now = datetime.now()
            expired_tokens = []

            for token_id, token_data in self.tokens.items():
                if 'expires_at' in token_data:
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at < now:
                        expired_tokens.append(token_id)

            for token_id in expired_tokens:
                del self.tokens[token_id]

            if expired_tokens:
                self._save_to_file()
                log.info(f"Cleaned up {len(expired_tokens)} expired tokens from file")

            return len(expired_tokens)

    def reload(self) -> None:
        """Reload tokens from the file."""
        with self.lock:
            self._load_from_file()
            log.info("Tokens reloaded from file")