"""Gemini + SQLite server example using the Chinook sample database."""

from __future__ import annotations

import os
from pathlib import Path

from vanna import Agent, AgentConfig
from vanna.capabilities.agent_memory import AgentMemory
from vanna.core.registry import ToolRegistry
from vanna.core.user import RequestContext, User, UserResolver
from vanna.integrations.google import GeminiLlmService
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools import RunSqlTool


class DemoUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="demo-user", username="demo", email="demo@example.com")


def create_demo_agent() -> Agent:
    database_path = Path(__file__).resolve().parents[3] / "Chinook.sqlite"
    if not database_path.exists():
        raise FileNotFoundError(
            f"Database not found at {database_path}. "
            "Download it from https://vanna.ai/Chinook.sqlite"
        )

    tools = ToolRegistry()
    tools.register_local_tool(
        RunSqlTool(sql_runner=SqliteRunner(str(database_path))), []
    )

    agent_memory: AgentMemory = DemoAgentMemory()
    return Agent(
        llm_service=GeminiLlmService(
            model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        ),
        tool_registry=tools,
        user_resolver=DemoUserResolver(),
        agent_memory=agent_memory,
        config=AgentConfig(stream_responses=True),
    )
