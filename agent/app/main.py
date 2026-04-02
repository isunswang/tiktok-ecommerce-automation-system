"""Agent service entry point (FastAPI wrapper)."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import agent_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Agent service starting, LLM model: {agent_settings.llm_model}")
    yield
    print("Agent service shutting down...")


app = FastAPI(
    title="TikTok Ops Agent Service",
    description="LangGraph Agent orchestration service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent", "model": agent_settings.llm_model}


@app.post("/api/v1/agent/run")
async def run_agent(task_type: str, context: dict = {}):
    """Execute an agent task."""
    from app.graph.workflow import create_workflow

    graph = create_workflow()
    result = await graph.ainvoke({
        "task_type": task_type,
        "product_data": context.get("product_data", {}),
        "messages": [],
        "current_agent": "",
        "error": "",
    })
    return result
