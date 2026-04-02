"""LangGraph workflow state definition using TypedDict."""

from typing import Any, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """State structure passed between graph nodes.

    This TypedDict defines the shared state that all agents
    in the workflow can read from and write to.
    """

    # Task identification
    task_type: str                          # selection/listing/fulfillment/cs/finance
    task_id: str                            # Unique task identifier

    # Data payloads (populated by different agents)
    product_data: dict[str, Any]            # Product info from selection/DB
    material_data: dict[str, Any]           # Generated materials (titles/descriptions/images)
    pricing_data: dict[str, Any]            # Pricing calculation results
    listing_result: dict[str, Any]          # TikTok listing result
    order_data: dict[str, Any]              # Order information
    fulfillment_data: dict[str, Any]        # Fulfillment/purchase/shipping info
    finance_data: dict[str, Any]            # Financial records/reports

    # Communication
    messages: list[BaseMessage]             # Agent conversation messages
    current_agent: str                      # Name of currently executing agent

    # Error handling
    error: str                              # Error message if any
    retry_count: int                        # Number of retries for current task

    # Metadata
    created_at: str                         # ISO timestamp of task creation
    updated_at: str                         # ISO timestamp of last update
