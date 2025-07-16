import json
import os
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions.state import State
from google.adk.tools import ToolContext

from coordination_agent.shared_libraries import constants

INITIAL_STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "initial_state.json")
USER_PROFILES_SEED_FILE = os.getenv("USER_PROFILES_SEED")


def memorize(key: str, value: dict, tool_context: ToolContext):
    """
    Memorize pieces of information, one key-value pair at a time.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    mem_dict = tool_context.state
    mem_dict[key] = value
    return {"status": f"Stored '{key}': '{value}'"}


def forget(key: str, value: dict, tool_context: ToolContext):
    """
    Remove pieces of information from state.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be removed.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    if tool_context.state[key] is None:
        tool_context.state[key] = []
    if value in tool_context.state[key]:
        tool_context.state[key].remove(value)
    return {"status": f"Removed '{key}': '{value}'"}


def _set_initial_states(source: dict[str, Any], target: State | dict[str, Any]):
    """
    Setting the initial session state given a JSON object of states.

    Args:
        source: A JSON object of states.
        target: The session state object to insert into.
    """
    target.update(source)


def load_initial_state(callback_context: CallbackContext):
    """
    Sets up the initial state. Use as a callback as for `before_agent_call` of the root_agent.

    Args:
        callback_context: The callback context.
    """
    init_state = {}
    with open(INITIAL_STATE_FILE, "r") as file:
        init_state = json.load(file)
        print(f"\nLoading Initial State: {init_state}\n")

    _set_initial_states(init_state[constants.STATE], callback_context.state)

    # Seed with user profiles
    with open(USER_PROFILES_SEED_FILE, "r") as file:
        p = json.load(file)
        profiles = { constants.USER_PROFILES: p }
        print(f"\nLoading Initial Profiles Seed...\n")

    _set_initial_states(profiles, callback_context.state)
