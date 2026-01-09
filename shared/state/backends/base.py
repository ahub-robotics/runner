"""
Abstract Base Class for State Storage Backends

Defines the interface that all state backends must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional


class StateBackend(ABC):
    """Abstract base class for state storage backends."""

    @abstractmethod
    def hset(self, key: str, mapping: dict) -> int:
        """
        Set multiple fields in a hash.

        Args:
            key: The hash key
            mapping: Dictionary of field:value pairs

        Returns:
            Number of fields set
        """
        pass

    @abstractmethod
    def hgetall(self, key: str) -> dict:
        """
        Get all fields and values from a hash.

        Args:
            key: The hash key

        Returns:
            Dictionary of field:value pairs
        """
        pass

    @abstractmethod
    def hget(self, key: str, field: str) -> Optional[str]:
        """
        Get a single field value from a hash.

        Args:
            key: The hash key
            field: The field name

        Returns:
            Field value or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> bool:
        """
        Set a key-value pair.

        Args:
            key: The key
            value: The value

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Get a value by key.

        Args:
            key: The key

        Returns:
            Value or None if not found
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> int:
        """
        Delete a key and all its data.

        Args:
            key: The key to delete

        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists.

        Args:
            key: The key

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    def keys(self, pattern: str = '*') -> list:
        """
        Get all keys matching a pattern.

        Args:
            pattern: Pattern to match (default: '*' for all keys)

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Test connectivity to the backend.

        Returns:
            True if connected and responsive
        """
        pass

    @abstractmethod
    def close(self):
        """Close connections and cleanup resources."""
        pass
