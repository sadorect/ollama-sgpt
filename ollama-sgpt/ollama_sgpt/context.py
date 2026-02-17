"""Context management for ollama-sgpt."""
from pathlib import Path
from typing import List, Optional


def load_context_files(file_paths: List[str]) -> str:
    """Load content from multiple files.
    
    Args:
        file_paths: List of file paths to load
        
    Returns:
        Combined content from all files with file markers
        
    Raises:
        FileNotFoundError: If any file doesn't exist
        IOError: If any file cannot be read
    """
    context_parts = []
    
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Context file not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add file marker for clarity
            context_parts.append(f"--- File: {file_path} ---")
            context_parts.append(content)
            context_parts.append("")  # Empty line separator
            
        except IOError as e:
            raise IOError(f"Cannot read context file {file_path}: {e}")
    
    return "\n".join(context_parts)


def build_context_prompt(user_input: str, context: Optional[str] = None) -> str:
    """Build prompt with optional context.
    
    Args:
        user_input: The user's question or request
        context: Optional context from loaded files
        
    Returns:
        Complete prompt with context prepended if provided
    """
    if context:
        return f"""Context information:

{context}

---

Based on the context above, please answer the following:

{user_input}"""
    
    return user_input


def format_context_summary(file_paths: List[str]) -> str:
    """Format a summary of loaded context files.
    
    Args:
        file_paths: List of file paths that were loaded
        
    Returns:
        Formatted summary string
    """
    if not file_paths:
        return "No context files loaded"
    
    summary_parts = [f"Loaded {len(file_paths)} context file(s):"]
    for i, file_path in enumerate(file_paths, 1):
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            summary_parts.append(f"  {i}. {file_path} ({size} bytes)")
        else:
            summary_parts.append(f"  {i}. {file_path} (not found)")
    
    return "\n".join(summary_parts)


def validate_context_files(file_paths: List[str]) -> tuple[List[str], List[str]]:
    """Validate which context files exist and are readable.
    
    Args:
        file_paths: List of file paths to validate
        
    Returns:
        Tuple of (valid_files, invalid_files)
    """
    valid_files = []
    invalid_files = []
    
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists() and path.is_file():
            try:
                # Test if we can read it
                with open(path, 'r', encoding='utf-8') as f:
                    f.read(1)  # Read just one byte to test
                valid_files.append(file_path)
            except Exception:
                invalid_files.append(file_path)
        else:
            invalid_files.append(file_path)
    
    return valid_files, invalid_files
