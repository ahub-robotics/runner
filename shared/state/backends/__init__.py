"""
State Storage Backends for Robot Runner

This package provides multiple backend implementations for state storage:
- RedisStateBackend: For Linux/macOS (fast, requires Redis)
- SQLiteStateBackend: For Windows (portable, no installation needed)

The appropriate backend is auto-selected based on the operating system.
"""
from .base import StateBackend
from .factory import get_state_backend

__all__ = ['StateBackend', 'get_state_backend']
