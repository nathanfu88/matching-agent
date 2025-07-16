"""Agent module for the root manager agent."""

import logging
import warnings
from datetime import datetime
from pathlib import Path
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext

from coordination_agent.sub_agents.matcher import matcher
from coordination_agent.sub_agents.scheduler.agent import scheduler
from coordination_agent.sub_agents.writer.agent import writer
from coordination_agent.shared_libraries.callbacks import (
    after_agent_trace,
    before_agent_trace,
)

from .prompts import ROOT_AGENT_INSTRUCTION
from .tools.memory import load_initial_state

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

# Configure logging to file
# Configure root logger
log_dir = Path("logs")
try:
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / f"{datetime.now().strftime("%Y%m%d_%H%M%S")}.log"
    
    # Clear existing handlers if any
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up file handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to the root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file.absolute()}")
    
except Exception as e:
    # Fallback to basic console logging if file logging fails
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize file logging: {e}")
    logger.info("Falling back to console logging only")

import litellm
litellm._turn_on_debug()

def before_agent_callback(callback_context: CallbackContext):
    load_initial_state(callback_context)
    before_agent_trace(callback_context)

    return None

root_agent = Agent(
    # model=LiteLlm(model="ollama_chat/llama3.1"),
    model=LiteLlm(model="openrouter/openai/gpt-4.1-nano"),
    # model=LiteLlm(model="openrouter/google/gemini-2.5-flash"),
    instruction=ROOT_AGENT_INSTRUCTION,
    name="radiance_assistant",
    description="Digital personal assistant specializing in meeting coordination and management",
    sub_agents=[
        matcher,    # Sub-agent for participant matching and grouping
        scheduler,  # Sub-agent for meeting scheduling and time coordination
        writer,     # Sub-agent for email drafting and communication
    ],
    after_agent_callback=after_agent_trace,
    before_agent_callback=before_agent_callback,
)
