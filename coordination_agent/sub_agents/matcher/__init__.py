"""
Matcher sub-agent module.

This module provides the matcher functionality through the `matcher` object.
Direct imports of this module are not allowed. Use `from coordination_agent.sub_agents.matcher import matcher` instead.
"""

from .agent import matcher_presenter as matcher

# Prevent direct imports of this module
if __name__ != 'coordination_agent.sub_agents.matcher':
    raise ImportError(
        "Direct imports of 'coordination_agent.sub_agents.matcher' are not allowed. "
        "Please use 'from coordination_agent.sub_agents.matcher import matcher' instead."
    )

__all__ = ['matcher']
