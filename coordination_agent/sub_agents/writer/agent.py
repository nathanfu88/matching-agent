"""Agent module for the writer agent."""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import INSTRUCTION
from coordination_agent.shared_libraries.callbacks import (
    before_agent_trace,
    after_agent_trace,
)

writer = Agent(
    # model=LiteLlm(model="ollama_chat/llama3.1"),
    # model=LiteLlm(model="openrouter/openai/gpt-4.1-nano"),
    model=LiteLlm(model="openrouter/google/gemini-2.5-flash"),
    name="writer",
    description="Specialized agent for drafting meeting invitations, emails, and communication content. Handles requests to compose, write, or generate meeting-related messages and invitations.",
    instruction=INSTRUCTION,
    before_agent_callback=before_agent_trace,
    after_agent_callback=after_agent_trace,
)
