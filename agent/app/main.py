"""Agent service entry point (FastAPI wrapper)."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import agent_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Agent service starting, LLM model: {agent_settings.llm_model}")
    print(f"TikTok mock mode: {agent_settings.tiktok_shop_mock_mode}")
    print(f"1688 mock mode: {agent_settings.alibaba_1688_mock_mode}")
    yield
    print("Agent service shutting down...")


app = FastAPI(
    title="TikTok Ops Agent Service",
    description="LangGraph Agent orchestration service",
    version="0.2.0",
    lifespan=lifespan,
)


# ==================== Request Models ====================

class RunAgentRequest(BaseModel):
    """Request to run a single agent task."""
    task_type: str
    context: dict[str, Any] = {}


class SelectionRequest(BaseModel):
    """Request for product selection."""
    products: list[dict[str, Any]]
    market_context: dict[str, Any] | None = None
    top_n: int = 10
    min_score: float = 50.0


class MaterialRequest(BaseModel):
    """Request for material generation."""
    product: dict[str, Any]
    target_market: str = "US"


class PricingRequest(BaseModel):
    """Request for pricing calculation."""
    product: dict[str, Any]
    market_context: dict[str, Any] | None = None


class ListingRequest(BaseModel):
    """Request for TikTok listing."""
    product: dict[str, Any]
    material_data: dict[str, Any] = {}
    pricing_data: dict[str, Any] = {}


class FullWorkflowRequest(BaseModel):
    """Request for full listing workflow."""
    product: dict[str, Any]
    target_market: str = "US"
    market_context: dict[str, Any] | None = None


# ==================== Health ====================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "agent",
        "model": agent_settings.llm_model,
        "tiktok_mock": agent_settings.tiktok_shop_mock_mode,
    }


# ==================== Workflow Endpoints ====================

@app.post("/api/v1/agent/run")
async def run_agent(request: RunAgentRequest):
    """Execute an agent task using LangGraph workflow."""
    from app.graph.workflow import create_workflow

    graph = create_workflow()
    result = await graph.ainvoke({
        "task_type": request.task_type,
        "product_data": request.context.get("product_data", {}),
        "order_data": request.context.get("order_data", {}),
        "messages": [],
        "current_agent": "",
        "error": "",
    })
    return result


@app.post("/api/v1/agent/full-workflow")
async def run_full_workflow(request: FullWorkflowRequest) -> dict[str, Any]:
    """Run the complete workflow: selection -> material -> pricing -> listing."""
    from app.graph.workflow import create_workflow

    graph = create_workflow()

    # Initialize state with all needed data
    initial_state = {
        "task_type": "listing",  # Full workflow ends with listing
        "product_data": {
            "product": request.product,
            "candidates": [request.product],
        },
        "target_market": request.target_market,
        "market_context": request.market_context or {},
        "messages": [],
        "current_agent": "",
        "error": "",
    }

    # Execute workflow
    result = await graph.ainvoke(initial_state)

    return {
        "task_id": result.get("task_id"),
        "product_data": result.get("product_data"),
        "material_data": result.get("material_data"),
        "pricing_data": result.get("pricing_data"),
        "listing_result": result.get("listing_result"),
        "error": result.get("error"),
    }


# ==================== Single Agent Endpoints ====================

@app.post("/api/v1/agent/selection")
async def run_selection_agent(request: SelectionRequest) -> dict[str, Any]:
    """Run only the selection agent to evaluate products."""
    from app.services.selection_service import selection_service

    try:
        ranked = await selection_service.rank_products(
            request.products,
            top_n=request.top_n,
            min_score=request.min_score,
        )

        return {
            "success": True,
            "total_evaluated": len(request.products),
            "total_recommended": len(ranked),
            "recommendations": [
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
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agent/material")
async def run_material_agent(request: MaterialRequest) -> dict[str, Any]:
    """Run only the material agent to generate content."""
    from app.services.material_service import material_service

    try:
        materials = await material_service.generate_full_materials(
            request.product,
            target_market=request.target_market,
        )
        return {"success": True, "materials": materials}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agent/pricing")
async def run_pricing_agent(request: PricingRequest) -> dict[str, Any]:
    """Run only the pricing agent to calculate prices."""
    from app.services.pricing_service import pricing_service

    try:
        pricing = await pricing_service.generate_pricing_suggestions(
            request.product,
            market_context=request.market_context or {},
        )
        return {"success": True, "pricing": pricing}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/agent/listing")
async def run_listing_agent(request: ListingRequest) -> dict[str, Any]:
    """Run the listing agent to create TikTok product."""
    from app.clients.tiktok_client import get_tiktok_client

    try:
        client = get_tiktok_client()

        # Match category if not provided
        category_id = None
        if not request.material_data.get("category_id"):
            product_name = request.material_data.get("titles", [{}])[0].get("title", request.product.get("title", ""))
            categories = await client.match_category(product_name)
            if categories:
                category_id = categories[0].get("id")
        else:
            category_id = request.material_data.get("category_id")

        # Prepare listing data
        listing_data = {
            "title": request.material_data.get("titles", [{}])[0].get("title", request.product.get("title")),
            "description": request.material_data.get("description", ""),
            "category_id": category_id,
            "images": [request.product.get("main_image_url")] if request.product.get("main_image_url") else [],
            "price": request.pricing_data.get("recommended_strategy", {}).get("price_local", "29.99"),
        }

        result = await client.create_product(listing_data)
        return {"success": True, "listing": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TikTok Direct Endpoints ====================

@app.get("/api/v1/tiktok/categories")
async def get_tiktok_categories(parent_id: str | None = None):
    """Get TikTok Shop categories."""
    from app.clients.tiktok_client import get_tiktok_client

    client = get_tiktok_client()
    categories = await client.get_categories(parent_id)
    return {"categories": categories}


@app.get("/api/v1/tiktok/orders")
async def get_tiktok_orders(status: str | None = None, page: int = 1):
    """Get TikTok Shop orders."""
    from app.clients.tiktok_client import get_tiktok_client

    client = get_tiktok_client()
    orders = await client.get_orders(status=status, page=page)
    return orders


@app.post("/api/v1/tiktok/match-category")
async def match_tiktok_category(product_name: str, description: str = ""):
    """Match product to TikTok categories."""
    from app.clients.tiktok_client import get_tiktok_client

    client = get_tiktok_client()
    matches = await client.match_category(product_name, description)
    return {"matches": matches}
