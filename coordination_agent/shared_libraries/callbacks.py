import logging
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext

logger = logging.getLogger(__name__)


def _lowercase_value(value):
    """Make dictionary lowercase"""
    if isinstance(value, dict):
        return (dict(k, _lowercase_value(v)) for k, v in value.items())
    elif isinstance(value, str):
        return value.lower()
    elif isinstance(value, (list, set, tuple)):
        tp = type(value)
        return tp(_lowercase_value(i) for i in value)
    else:
        return value


# Callback logging methods
def before_tool_trace(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
):
    # Make sure all values that the agent is sending to tools are lowercase to
    # improve predictability.
    _lowercase_value(args)

    tool_name = tool.name
    logger.info(f"[before_tool_trace] Running tool '{tool_name}'")
    logger.info(f"[before_tool_trace] With args: {args}")

    return None


def before_agent_trace(callback_context: CallbackContext):
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()
    logger.info(f"[before_agent_trace] Agent '{agent_name}' running with invocation_id '{invocation_id}'")
    logger.info(f"[before_agent_trace] With state: {current_state}")
    
    return None

def after_agent_trace(callback_context: CallbackContext):
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()
    logger.info(f"[after_agent_trace] Agent '{agent_name}' running with invocation_id '{invocation_id}'")
    logger.info(f"[after_agent_trace] With state: {current_state}")
    
    return None