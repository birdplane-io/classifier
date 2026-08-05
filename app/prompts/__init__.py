"""Prompts utilities."""
from pathlib import Path


def load_prompt(name: str) -> str:
    """
    Load a prompt file by name.
    
    Args:
        name: Prompt name (e.g., 'classifier' for 'classifier.md')
        
    Returns:
        Prompt content as string
        
    Raises:
        FileNotFoundError: If prompt file not found
    """
    prompt_dir = Path(__file__).parent
    prompt_file = prompt_dir / f"{name}.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_file}")
    
    return prompt_file.read_text()
