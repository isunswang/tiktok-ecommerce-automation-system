"""Agent registry - defines all available agents and their metadata."""

from typing import Any

AGENT_REGISTRY: dict[str, dict[str, Any]] = {
    "master": {
        "name": "Master Agent",
        "description": "全局调度Agent，负责任务分发和错误恢复",
        "node": "master_agent",
    },
    "selection": {
        "name": "选品Agent",
        "description": "负责1688商品搜索、评分和选品池管理",
        "node": "selection_agent",
    },
    "material": {
        "name": "素材Agent",
        "description": "负责AI生成商品标题、描述和图片优化",
        "node": "material_agent",
    },
    "pricing": {
        "name": "定价Agent",
        "description": "负责成本核算、定价建议和汇率管理",
        "node": "pricing_agent",
    },
    "listing": {
        "name": "上架Agent",
        "description": "负责TikTok类目匹配和商品上架",
        "node": "listing_agent",
    },
    "fulfillment": {
        "name": "履约Agent",
        "description": "负责1688采购下单、物流跟踪和发货管理",
        "node": "fulfillment_agent",
    },
    "customer_service": {
        "name": "客服Agent",
        "description": "负责AI自动应答、话术匹配和工单创建",
        "node": "customer_service_agent",
    },
    "finance": {
        "name": "财务Agent",
        "description": "负责财务对账、收入统计和利润报表",
        "node": "finance_agent",
    },
}


def get_agent(name: str) -> dict[str, Any] | None:
    """Get agent metadata by name."""
    return AGENT_REGISTRY.get(name)


def list_agents() -> list[dict[str, Any]]:
    """List all registered agents."""
    return list(AGENT_REGISTRY.values())
