"""
Version management for Robot Runner
"""

import os
import json
from pathlib import Path
from typing import Optional


class Version:
    """Semantic version handling"""

    def __init__(self, major: int, minor: int, patch: int, prerelease: str = ""):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease

    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        """
        Parse version from string like 'v2.0.1' or '2.0.1-beta'

        Examples:
            >>> Version.from_string('v2.0.1')
            Version(2, 0, 1)
            >>> Version.from_string('2.1.0-beta')
            Version(2, 1, 0, 'beta')
        """
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')

        # Split prerelease
        if '-' in version_str:
            version_part, prerelease = version_str.split('-', 1)
        else:
            version_part = version_str
            prerelease = ""

        # Parse major.minor.patch
        parts = version_part.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")

        major, minor, patch = map(int, parts)
        return cls(major, minor, patch, prerelease)

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version

    def __repr__(self) -> str:
        return f"Version({self.major}, {self.minor}, {self.patch}, '{self.prerelease}')"

    def __eq__(self, other: 'Version') -> bool:
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )

    def __lt__(self, other: 'Version') -> bool:
        """Compare versions (semantic versioning)"""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch

        # Prerelease versions are LOWER than release versions
        if not self.prerelease and other.prerelease:
            return False  # Stable > prerelease
        if self.prerelease and not other.prerelease:
            return True  # Prerelease < stable

        # Both have prereleases, compare alphabetically
        return self.prerelease < other.prerelease

    def __le__(self, other: 'Version') -> bool:
        return self == other or self < other

    def __gt__(self, other: 'Version') -> bool:
        return not self <= other

    def __ge__(self, other: 'Version') -> bool:
        return not self < other


def get_current_version() -> Version:
    """
    Get current version from version.json file

    Returns:
        Version object with current version

    Raises:
        FileNotFoundError: If version.json doesn't exist
        ValueError: If version format is invalid
    """
    # Look for version.json in multiple locations
    possible_locations = [
        Path.cwd() / "version.json",  # Current directory
        Path(__file__).parent.parent.parent / "version.json",  # Project root
        Path.home() / "Robot" / "version.json",  # Installation directory
    ]

    for location in possible_locations:
        if location.exists():
            try:
                with open(location, 'r') as f:
                    data = json.load(f)
                    return Version.from_string(data['version'])
            except (json.JSONDecodeError, KeyError) as e:
                continue

    # Default version if not found
    return Version(2, 0, 0)


def save_current_version(version: Version, location: Optional[Path] = None):
    """
    Save current version to version.json

    Args:
        version: Version object to save
        location: Optional custom location (defaults to cwd)
    """
    if location is None:
        location = Path.cwd() / "version.json"

    data = {
        "version": str(version),
        "major": version.major,
        "minor": version.minor,
        "patch": version.patch,
        "prerelease": version.prerelease
    }

    with open(location, 'w') as f:
        json.dump(data, f, indent=2)