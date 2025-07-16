from google.adk.evaluation.agent_evaluator import AgentEvaluator

import os
import pytest
from dotenv import find_dotenv, load_dotenv

@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv(find_dotenv(".env"))


@pytest.mark.asyncio
async def test_eval_single_step_triggers():
    """Test the agent's single-step trigger recognition (matcher/scheduler/writer)."""
    await AgentEvaluator.evaluate(
        "coordination_agent",
        os.path.join(
            os.path.dirname(__file__), "eval_data/evalset23fe92.evalset.json"
        ),
        num_runs=1,
    )
