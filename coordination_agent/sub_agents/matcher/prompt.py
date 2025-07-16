import os
from pathlib import Path

from coordination_agent.shared_libraries.types import MatcherResponse

def load_instruction_from_file(instruction_file_path=None):
    """
    Load instruction text from file at runtime.
    
    Args:
        instruction_file_path (str): Path to instruction file. If None, uses MATCHER_INSTRUCTION_FILE env var
        
    Returns:
        str: The instruction content
    """
    if instruction_file_path is None:
        instruction_file_path = os.getenv("MATCHER_INSTRUCTION_FILE")
        
    # Handle relative paths from project root
    if not os.path.isabs(instruction_file_path):
        # Assume relative to project root (where .env file typically is)
        project_root = Path(__file__).parent.parent.parent.parent
        instruction_file_path = project_root / instruction_file_path
    else:
        instruction_file_path = Path(instruction_file_path)
    
    try:
        with open(instruction_file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Instruction file not found: {instruction_file_path}")

# Load instruction from environment variable or default
INSTRUCTION = load_instruction_from_file()

PRESENTER_INSTRUCTION = f"""
You are an expert talent matcher who analyzes individual profiles and creates new meeting groups from scratch using a reasoning-based approach. Your role focuses on GROUP FORMATION rather than working with existing groups.

Use the `matcher` tool to create new groups from the individual pool. Always use this tool instead of trying to create groups on your own.

The response of the `matcher` tool is a structured JSON object:
{MatcherResponse.model_json_schema()}

Given the schema of the response of the `matcher` tool, present the response in a clear and concise manner in natural language to the user.
"""
