"""LangGraph graph nodes - each node is an agent entry point."""

import logging
from datetime import datetime, timezone

from langchain_core.messages import AIMessage

from app.graph.state import AgentState
from app.prompts.system_prompts import get_system_prompt
from app.services.selection_service import selection_service
from app.services.material_service import material_service
from app.services.pricing_service import pricing_service
from app.clients.tiktok_client import get_tiktok_client

logger = logging.getLogger(__name__)


async def master_agent_node(state: AgentState) -> dict:
    """Master Agent: route tasks to specialized agents.

    This node analyzes the task_type and dispatches to the appropriate
    specialized agent. It also handles error recovery and retry logic.
    """
    task_type = state.get("task_type", "")
    logger.info(f"Master Agent routing task: {task_type}")

    if not state.get("task_id"):
        state["task_id"] = f"task_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    if not state.get("created_at"):
        state["created_at"] = datetime.now(timezone.utc).isoformat()

    state["current_agent"] = "master"
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["retry_count"] = state.get("retry_count", 0) + 1

    return state


async def selection_agent_node(state: AgentState) -> dict:
    """Selection Agent: search and evaluate products from 1688.

    Uses LLM to score products across multiple dimensions:
    - Price competitiveness
    - Profit margin potential
    - Market demand
    - Supplier reliability
    """
    logger.info("Selection Agent: evaluating products")
    state["current_agent"] = "selection"

    product_data = state.get("product_data", {})
    products = product_data.get("candidates", [])

    if not products:
        # No products to evaluate
        state["product_data"] = {
            "candidates": [],
            "total_found": 0,
            "top_recommendations": [],
        }
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return state

    try:
        # Score and rank products
        ranked = await selection_service.rank_products(
            products,
            top_n=10,
            min_score=50.0,
        )

        # Format results
        top_recommendations = [
            {
                "product": p,
                "score": {
                    "overall": s.overall_score,
                    "price": s.price_score,
                    "profit": s.profit_score,
                    "demand": s.demand_score,
                    "supplier": s.supplier_score,
                    "reasoning": s.reasoning,
                    "recommendation": s.recommendation,
                },
            }
            for p, s in ranked
        ]

        state["product_data"] = {
            "candidates": products,
            "total_found": len(products),
            "top_recommendations": top_recommendations,
            "evaluation_summary": f"Evaluated {len(products)} products, {len(ranked)} recommended",
        }

        # Add message
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Selection complete: {len(ranked)} products recommended from {len(products)} candidates")
        ]

    except Exception as e:
        logger.error(f"Selection agent error: {e}", exc_info=True)
        state["error"] = str(e)

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state


async def material_agent_node(state: AgentState) -> dict:
    """Material Agent: generate AI titles, descriptions, and optimize images."""
    logger.info("Material Agent: generating product materials")
    state["current_agent"] = "material"

    product_data = state.get("product_data", {})
    product = product_data.get("product", product_data.get("candidates", [{}])[0] if product_data.get("candidates") else {})
    target_market = state.get("target_market", "US")

    if not product:
        state["material_data"] = {"error": "No product data provided"}
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return state

    try:
        # Generate all materials
        materials = await material_service.generate_full_materials(
            product,
            target_market=target_market,
        )

        state["material_data"] = materials

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Materials generated: {len(materials.get('titles', []))} titles, {len(materials.get('selling_points', []))} selling points")
        ]

    except Exception as e:
        logger.error(f"Material agent error: {e}", exc_info=True)
        state["error"] = str(e)
        state["material_data"] = {"error": str(e)}

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state


async def pricing_agent_node(state: AgentState) -> dict:
    """Pricing Agent: calculate costs and suggest pricing."""
    logger.info("Pricing Agent: calculating pricing")
    state["current_agent"] = "pricing"

    product_data = state.get("product_data", {})
    product = product_data.get("product", product_data.get("candidates", [{}])[0] if product_data.get("candidates") else {})
    market_context = state.get("market_context", {})

    if not product:
        state["pricing_data"] = {"error": "No product data provided"}
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return state

    try:
        # Generate pricing suggestions
        pricing_result = await pricing_service.generate_pricing_suggestions(
            product,
            market_context=market_context,
        )

        state["pricing_data"] = pricing_result

        recommended = pricing_result.get("recommended_strategy", {})
        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Pricing complete: recommended ${recommended.get('price_local', 'N/A')} ({recommended.get('profit_rate', 'N/A')} profit)")
        ]

    except Exception as e:
        logger.error(f"Pricing agent error: {e}", exc_info=True)
        state["error"] = str(e)
        state["pricing_data"] = {"error": str(e)}

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state


async def listing_agent_node(state: AgentState) -> dict:
    """Listing Agent: match categories and list products on TikTok Shop."""
    logger.info("Listing Agent: listing product on TikTok Shop")
    state["current_agent"] = "listing"

    product_data = state.get("product_data", {})
    material_data = state.get("material_data", {})
    pricing_data = state.get("pricing_data", {})

    product = product_data.get("product", product_data.get("candidates", [{}])[0] if product_data.get("candidates") else {})

    if not product:
        state["listing_result"] = {"error": "No product data provided"}
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return state

    try:
        client = get_tiktok_client()

        # Step 1: Match category
        product_name = material_data.get("titles", [{}])[0].get("title", product.get("title", ""))
        categories = await client.match_category(product_name)

        if not categories:
            state["listing_result"] = {"error": "No matching category found"}
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            return state

        best_category = categories[0]

        # Step 2: Prepare listing data
        listing_data = {
            "title": material_data.get("titles", [{}])[0].get("title", product.get("title")),
            "description": material_data.get("description", ""),
            "category_id": best_category.get("id"),
            "images": [product.get("main_image_url")] if product.get("main_image_url") else [],
            "price": pricing_data.get("recommended_strategy", {}).get("price_local", "29.99"),
        }

        # Step 3: Create product on TikTok
        result = await client.create_product(listing_data)

        state["listing_result"] = {
            "tiktok_product_id": result.get("product_id"),
            "status": result.get("status"),
            "category_matched": best_category,
            "message": result.get("message", "Listing complete"),
        }

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=f"Product listed: {result.get('product_id')} in category {best_category.get('name')}")
        ]

    except Exception as e:
        logger.error(f"Listing agent error: {e}", exc_info=True)
        state["error"] = str(e)
        state["listing_result"] = {"error": str(e)}

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state


async def fulfillment_agent_node(state: AgentState) -> dict:
    """Fulfillment Agent: create purchase orders and track shipments."""
    logger.info("Fulfillment Agent: processing fulfillment")
    state["current_agent"] = "fulfillment"

    order_data = state.get("order_data", {})

    if not order_data:
        state["fulfillment_data"] = {"error": "No order data provided"}
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return state

    try:
        # TODO: Implement actual fulfillment logic
        # 1. Match order to 1688 supplier
        # 2. Create purchase order
        # 3. Track shipment

        state["fulfillment_data"] = {
            "purchase_order_id": None,
            "shipment_status": "pending",
            "tracking_info": [],
            "message": "Fulfillment processing (placeholder)",
        }

        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Fulfillment initiated for order")
        ]

    except Exception as e:
        logger.error(f"Fulfillment agent error: {e}", exc_info=True)
        state["error"] = str(e)

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state


async def customer_service_agent_node(state: AgentState) -> dict:
    """Customer Service Agent: handle buyer inquiries."""
    logger.info("Customer Service Agent: handling buyer inquiry")
    state["current_agent"] = "customer_service"

    inquiry = state.get("inquiry", "")

    if not inquiry:
        state["messages"] = state.get("messages", []) + [
            AIMessage(content="No inquiry to process")
        ]
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        return state

    try:
        # TODO: Implement actual CS logic with RAG
        # 1. Match inquiry to FAQ
        # 2. Generate response
        # 3. Escalate if needed

        response = f"Thank you for your inquiry. We're processing your request: '{inquiry[:50]}...'"

        state["messages"] = state.get("messages", []) + [
            AIMessage(content=response)
        ]

    except Exception as e:
        logger.error(f"Customer service agent error: {e}", exc_info=True)
        state["error"] = str(e)

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state


async def finance_agent_node(state: AgentState) -> dict:
    """Finance Agent: generate financial reports and reconciliation."""
    logger.info("Finance Agent: processing financial data")
    state["current_agent"] = "finance"

    try:
        # TODO: Implement actual finance logic
        # 1. Calculate revenue/costs
        # 2. Generate profit report
        # 3. Currency exchange

        state["finance_data"] = {
            "summary": {},
            "transactions": [],
            "message": "Finance processing (placeholder)",
        }

        state["messages"] = state.get("messages", []) + [
            AIMessage(content="Finance report generated")
        ]

    except Exception as e:
        logger.error(f"Finance agent error: {e}", exc_info=True)
        state["error"] = str(e)

    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return state
