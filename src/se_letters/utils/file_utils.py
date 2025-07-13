"""File utility functions for the SE Letters project."""

import hashlib
import re
from pathlib import Path
from typing import Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path.
        
    Returns:
        Path object for the directory.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_hash(
    file_path: Union[str, Path], algorithm: str = "sha256"
) -> str:
    """Get hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.
        
    Returns:
        Hex digest of the file hash.
    """
    file_path = Path(file_path)
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def safe_filename(filename: str, max_length: int = 255) -> str:
    """Create a safe filename by removing invalid characters.
    
    Args:
        filename: Original filename.
        max_length: Maximum filename length.
        
    Returns:
        Safe filename.
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', "", filename)
    
    # Trim whitespace and dots
    filename = filename.strip(". ")
    
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    # Truncate if too long
    if len(filename) > max_length:
        parts = filename.rsplit(".", 1) if "." in filename else (filename, "")
        name, ext = parts
        max_name_len = max_length - len(ext) - 1 if ext else max_length
        filename = name[:max_name_len] + ("." + ext if ext else "")
    
    return filename


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in megabytes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        File size in MB.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return 0.0
    
    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 * 1024)


def is_file_empty(file_path: Union[str, Path]) -> bool:
    """Check if a file is empty.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        True if file is empty or doesn't exist.
    """
    file_path = Path(file_path)
    return not file_path.exists() or file_path.stat().st_size == 0 