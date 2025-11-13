# This file contains helper functions for agents
from pathlib import Path

def load_instructions(filename: str) -> str:
    """Load instructions from a given file."""
    # Get the directory where this helper.py file is located
    current_dir = Path(__file__).parent
    instructions_path = current_dir / "instructions" / f"{filename}.txt"
    
    with open(instructions_path, 'r') as file:
        instructions = file.read()
    return instructions
