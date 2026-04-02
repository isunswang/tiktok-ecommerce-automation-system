"""Basic workflow test."""

import asyncio
import pytest

from app.graph.workflow import create_workflow


@pytest.mark.asyncio
async def test_workflow_creation():
    """Test that the workflow graph can be created and compiled."""
    graph = create_workflow()
    assert graph is not None


@pytest.mark.asyncio
async def test_workflow_listing_task():
    """Test workflow execution with a listing task type."""
    graph = create_workflow()
    result = await graph.ainvoke({
        "task_type": "listing",
        "messages": [],
        "current_agent": "",
        "error": "",
    })
    assert result is not None
    assert result.get("current_agent") == "listing"
    assert result.get("error") == ""


@pytest.mark.asyncio
async def test_workflow_selection_task():
    """Test workflow execution with a selection task type."""
    graph = create_workflow()
    result = await graph.ainvoke({
        "task_type": "selection",
        "messages": [],
        "current_agent": "",
        "error": "",
    })
    assert result is not None
    assert result.get("current_agent") == "selection"


@pytest.mark.asyncio
async def test_agent_registry():
    """Test that agent registry returns correct metadata."""
    from app.agents import get_agent, list_agents

    agents = list_agents()
    assert len(agents) == 8

    master = get_agent("master")
    assert master is not None
    assert master["name"] == "Master Agent"


@pytest.mark.asyncio
async def test_system_prompts():
    """Test that system prompts are defined for all agents."""
    from app.prompts.system_prompts import get_system_prompt

    for agent_name in ["master", "selection", "material", "pricing",
                       "listing", "fulfillment", "customer_service", "finance"]:
        prompt = get_system_prompt(agent_name)
        assert prompt is not None
        assert len(prompt) > 50
