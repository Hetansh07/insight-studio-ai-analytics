"""
Mock quickstart example for the Vanna Agents framework.

This example shows how to create a basic agent with a mock LLM service
and have a simple conversation.

Usage:
  Template: Copy this file and modify for your needs
  Interactive: python -m vanna.examples.mock_quickstart
  REPL: from vanna.examples.mock_quickstart import create_demo_agent
  Server: python -m vanna.servers --example mock_quickstart
"""

import asyncio
from pathlib import Path

from vanna import (
    AgentConfig,
    Agent,
    MockLlmService,
)
from vanna.capabilities.agent_memory import AgentMemory
from vanna.core.user import RequestContext, User, UserResolver
from vanna.core.registry import ToolRegistry
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.local.file_system import LocalFileSystem
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools import ProfileTableTool, RunSqlTool, VisualizeDataTool


class DemoUserResolver(UserResolver):
    """Resolve every demo request to a local test user."""

    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(
            id="demo-user",
            username="demo",
            email="demo@example.com",
        )


def create_demo_agent() -> Agent:
    """Create a demo agent for REPL and server usage.

    Returns:
        Configured Agent instance
    """
    llm_service = MockLlmService(
        response_content="Hello! I'm a helpful AI assistant created using the Vanna Agents framework."
    )

    agent_memory: AgentMemory = DemoAgentMemory()

    tool_registry = ToolRegistry()
    file_system = LocalFileSystem()
    database_path = Path(__file__).resolve().parents[3] / "Chinook.sqlite"
    if database_path.exists():
        tool_registry.register_local_tool(
            RunSqlTool(
                sql_runner=SqliteRunner(str(database_path)),
                file_system=file_system,
            ),
            [],
        )
        tool_registry.register_local_tool(
            ProfileTableTool(sql_runner=SqliteRunner(str(database_path))),
            [],
        )
        tool_registry.register_local_tool(VisualizeDataTool(file_system=file_system), [])

    return Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        user_resolver=DemoUserResolver(),
        agent_memory=agent_memory,
        config=AgentConfig(
            stream_responses=True,  # Enable streaming for better server experience
            include_thinking_indicators=True,
        ),
    )


async def main() -> None:
    """Run the mock quickstart example."""

    # Create agent using factory function
    agent = create_demo_agent()

    # Create a test user
    user = User(
        id="user123", username="testuser", email="test@example.com", permissions=[]
    )

    # Start a conversation
    conversation_id = "conversation123"
    user_message = "Hello! Can you introduce yourself?"

    print(f"User: {user_message}")
    print("Agent: ", end="")

    # Send message and collect response
    async for component in agent.send_message(
        user=user, message=user_message, conversation_id=conversation_id
    ):
        if hasattr(component, "content"):
            print(component.content, end="")

    print()


def run_interactive() -> None:
    """Entry point for interactive usage."""
    print("Starting Vanna Agents mock quickstart demo...")
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()
