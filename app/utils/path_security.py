"""Path security utilities to prevent path traversal attacks."""
import os
from pathlib import Path
from typing import Union


def validate_safe_path(user_path: str, base_directory: Union[str, Path]) -> Path:
    """
    Validate that a user - provided path is safe and within the base directory.

    Args:
        user_path: User - provided path (potentially malicious)
        base_directory: Base directory to restrict access to

    Returns:
        Resolved safe path

    Raises:
        ValueError: If path traversal attempt detected
    """
    # Convert to Path objects and resolve
    base_dir = Path(base_directory).resolve()

    # Remove any path separators and resolve the user path
    # This prevents ../../../etc/passwd type attacks
    safe_name = os.path.basename(user_path)
    target_path = (base_dir / safe_name).resolve()

    # Ensure the resolved path is within the base directory
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise ValueError(f"Path traversal attempt detected: {user_path}")

    return target_path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', '..', '~', '|', ':', '*', '?', '"', '<', '>', '\0']
    sanitized = filename

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:250] + ext

    if not sanitized:
        raise ValueError("Filename becomes empty after sanitization")

    return sanitized


def is_safe_path(file_path: Union[str, Path], allowed_directories: list) -> bool:
    """
    Check if a file path is within allowed directories.

    Args:
        file_path: Path to check
        allowed_directories: List of allowed base directories

    Returns:
        True if path is safe, False otherwise
    """
    try:
        resolved_path = Path(file_path).resolve()

        for allowed_dir in allowed_directories:
            allowed_path = Path(allowed_dir).resolve()
            try:
                resolved_path.relative_to(allowed_path)
                return True
            except ValueError:
                continue

        return False
    except Exception:
        return False
