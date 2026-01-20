"""
Checksum verification for downloaded updates
"""

import hashlib
from pathlib import Path
from typing import Union


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA256 checksum of a file

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal SHA256 checksum

    Example:
        >>> calculate_sha256('RobotRunner.exe')
        'a3b5c7d9e1f2...'
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()

    # Read file in chunks to handle large files
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify file integrity against expected checksum

    Args:
        file_path: Path to file to verify
        expected_checksum: Expected SHA256 checksum (hex string)

    Returns:
        True if checksums match, False otherwise

    Example:
        >>> verify_checksum('RobotRunner.exe', 'a3b5c7d9e1f2...')
        True
    """
    try:
        actual_checksum = calculate_sha256(file_path)
        return actual_checksum.lower() == expected_checksum.lower().strip()
    except Exception as e:
        print(f"Error verifying checksum: {e}")
        return False


def read_checksum_file(checksum_file: Union[str, Path]) -> str:
    """
    Read checksum from .sha256 file

    Args:
        checksum_file: Path to .sha256 file

    Returns:
        Checksum string

    Example:
        >>> read_checksum_file('RobotRunner.exe.sha256')
        'a3b5c7d9e1f2...'
    """
    checksum_file = Path(checksum_file)

    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")

    with open(checksum_file, 'r') as f:
        # Read first line and strip whitespace
        checksum = f.readline().strip()

        # Some checksum files have format: "checksum  filename"
        # Extract just the checksum part
        if ' ' in checksum:
            checksum = checksum.split()[0]

        return checksum


def verify_with_checksum_file(
    file_path: Union[str, Path],
    checksum_file: Union[str, Path]
) -> bool:
    """
    Verify file against checksum file

    Args:
        file_path: Path to file to verify
        checksum_file: Path to .sha256 file

    Returns:
        True if checksums match, False otherwise

    Example:
        >>> verify_with_checksum_file('RobotRunner.exe', 'RobotRunner.exe.sha256')
        True
    """
    try:
        expected_checksum = read_checksum_file(checksum_file)
        return verify_checksum(file_path, expected_checksum)
    except Exception as e:
        print(f"Error verifying with checksum file: {e}")
        return False