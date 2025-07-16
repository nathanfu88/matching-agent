"""Agent module for the matcher agent."""

import litellm
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from .prompt import INSTRUCTION, PRESENTER_INSTRUCTION
from coordination_agent.shared_libraries.callbacks import (
    before_agent_trace,
    after_agent_trace,
)
from coordination_agent.shared_libraries.constants import MATCHED_GROUPS
from coordination_agent.shared_libraries.types import MatcherResponse

litellm._turn_on_debug()


matcher = Agent(
    # model=LiteLlm(model="ollama_chat/llama3.1"),
    # model=LiteLlm(model="openrouter/openai/gpt-4.1-nano"),
    model=LiteLlm(model="openrouter/google/gemini-2.5-flash"),
    name="matcher",
    description="Core specialized agent for participant matching and grouping.",
    instruction=INSTRUCTION,
    before_agent_callback=before_agent_trace,
    after_agent_callback=after_agent_trace,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key=MATCHED_GROUPS,
    output_schema=MatcherResponse,
)

matcher_presenter = Agent(
    model=LiteLlm(model="openrouter/google/gemini-2.5-flash"),
    name="matcher_presenter",
    description="Specialized agent for participant matching, grouping, and pairing for meetings. Handles requests to organize people into optimal meeting combinations based on compatibility and needs.",
    instruction=PRESENTER_INSTRUCTION,
    before_agent_callback=before_agent_trace,
    after_agent_callback=after_agent_trace,
    tools=[
        AgentTool(matcher),
    ],
)
