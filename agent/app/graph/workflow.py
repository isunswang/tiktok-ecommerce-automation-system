"""LangGraph StateGraph workflow definition.

Defines the main workflow that orchestrates all agents.
Uses conditional edges to route between agents based on task_type.
"""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    customer_service_agent_node,
    finance_agent_node,
    fulfillment_agent_node,
    listing_agent_node,
    master_agent_node,
    material_agent_node,
    pricing_agent_node,
    selection_agent_node,
)
from app.graph.state import AgentState


def route_by_task_type(state: AgentState) -> str:
    """Conditional routing function based on task_type.

    Determines which agent should handle the current task.
    """
    task_type = state.get("task_type", "")
    routing_map = {
        "selection": "selection_agent",
        "material": "material_agent",
        "pricing": "pricing_agent",
        "listing": "listing_agent",
        "fulfillment": "fulfillment_agent",
        "customer_service": "customer_service_agent",
        "finance": "finance_agent",
    }
    return routing_map.get(task_type, "listing_agent")


def create_workflow() -> StateGraph:
    """Create and compile the main agent workflow graph.

    Workflow structure:
        START -> master_agent -> [conditional: task_type] -> specialized_agent -> END

    For multi-step workflows (e.g., selection -> material -> pricing -> listing),
    agents can chain by updating the state and triggering subsequent nodes.
    """
    workflow = StateGraph(AgentState)

    # Add all agent nodes
    workflow.add_node("master_agent", master_agent_node)
    workflow.add_node("selection_agent", selection_agent_node)
    workflow.add_node("material_agent", material_agent_node)
    workflow.add_node("pricing_agent", pricing_agent_node)
    workflow.add_node("listing_agent", listing_agent_node)
    workflow.add_node("fulfillment_agent", fulfillment_agent_node)
    workflow.add_node("customer_service_agent", customer_service_agent_node)
    workflow.add_node("finance_agent", finance_agent_node)

    # Entry point: START -> master_agent
    workflow.add_edge(START, "master_agent")

    # Conditional routing from master_agent
    workflow.add_conditional_edges(
        "master_agent",
        route_by_task_type,
        {
            "selection_agent": "selection_agent",
            "material_agent": "material_agent",
            "pricing_agent": "pricing_agent",
            "listing_agent": "listing_agent",
            "fulfillment_agent": "fulfillment_agent",
            "customer_service_agent": "customer_service_agent",
            "finance_agent": "finance_agent",
        },
    )

    # All specialized agents -> END
    for agent in [
        "selection_agent",
        "material_agent",
        "pricing_agent",
        "listing_agent",
        "fulfillment_agent",
        "customer_service_agent",
        "finance_agent",
    ]:
        workflow.add_edge(agent, END)

    # Compile the graph
    return workflow.compile()
