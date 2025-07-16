import logging
import litellm
from google.adk import Agent
from google.adk.tools import BaseTool, ToolContext
from google.adk.models.lite_llm import LiteLlm
from typing import Any, Optional

from .prompt import INSTRUCTION
from .tools import (
  fetch_time_availabilities,
  get_meet_times,
)
from coordination_agent.shared_libraries.callbacks import (
    before_tool_trace,
    before_agent_trace,
    after_agent_trace,
)
from coordination_agent.shared_libraries.constants import (
    FETCH_TIME_AVAILABILITIES,
    GET_MEET_TIMES,
    MEETING_TIMES,
    USER_AVAILABILITIES,
)
from coordination_agent.tools.memory import memorize

logger = logging.getLogger(__name__)
litellm._turn_on_debug()

def after_tool_callback(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: dict
) -> Optional[dict]:
    tool_name = tool.name
    logger.info(f"Run tool '{tool_name}'")
    logger.debug(f"With args: {args}")
    logger.debug(f"With tool_response: {tool_response}")

    if tool_name == FETCH_TIME_AVAILABILITIES:
        availabilities = tool_response.get("result", {})
        memorize(USER_AVAILABILITIES, availabilities, tool_context)
        logger.debug(f"Updated state with user availabilities: {tool_context.state.__dict__}")

    if tool_name == GET_MEET_TIMES:
        meeting_times = tool_response.get("result", {})
        memorize(MEETING_TIMES, meeting_times, tool_context)
        logger.debug(f"Updated state with meeting times: {tool_context.state.__dict__}")

    return None


scheduler = Agent(
    # model=LiteLlm(model="ollama_chat/llama3.1"),
    # model=LiteLlm(model="openrouter/openai/gpt-4.1-nano"),
    model=LiteLlm(model="openrouter/google/gemini-2.5-flash"),
    name="scheduler",
    description="Specialized agent for meeting scheduling, time coordination, and availability management. Handles requests to find meeting times, check availability, and coordinate schedules between participants.",
    tools=[
        fetch_time_availabilities,
        get_meet_times,
    ],
    instruction=INSTRUCTION,
    before_agent_callback=before_agent_trace,
    after_agent_callback=after_agent_trace,
    before_tool_callback=before_tool_trace,
    after_tool_callback=after_tool_callback,
)
