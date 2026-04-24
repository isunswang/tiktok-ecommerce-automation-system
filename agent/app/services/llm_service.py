"""LLM service layer - unified interface for language model calls."""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import agent_settings

logger = logging.getLogger(__name__)

_llm_instance = None


def get_llm() -> ChatOpenAI:
    """Get or create the LLM instance (singleton)."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOpenAI(
            model=agent_settings.llm_model,
            api_key=agent_settings.llm_api_key,
            base_url=agent_settings.llm_base_url,
            temperature=agent_settings.llm_temperature,
        )
        logger.info(f"LLM initialized: model={agent_settings.llm_model}")
    return _llm_instance


async def llm_invoke(
    system_prompt: str,
    user_message: str,
    json_mode: bool = False,
) -> str:
    """Invoke LLM with system and user messages.

    Args:
        system_prompt: System prompt for the agent
        user_message: User message / task description
        json_mode: Whether to request JSON output

    Returns:
        LLM response text
    """
    llm = get_llm()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    if json_mode:
        llm = llm.bind(response_format={"type": "json_object"})

    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}", exc_info=True)
        raise


async def llm_invoke_json(
    system_prompt: str,
    user_message: str,
) -> dict[str, Any]:
    """Invoke LLM and parse response as JSON.

    Args:
        system_prompt: System prompt for the agent
        user_message: User message / task description

    Returns:
        Parsed JSON dictionary
    """
    # Add JSON instruction to the prompt
    enhanced_prompt = (
        f"{system_prompt}\n\n"
        "重要：你必须返回合法的JSON格式数据，不要包含任何其他文字说明。"
    )

    response = await llm_invoke(enhanced_prompt, user_message, json_mode=True)

    try:
        # Try to extract JSON from response
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}\nResponse: {response[:500]}")
        raise ValueError(f"LLM returned invalid JSON: {e}") from e
