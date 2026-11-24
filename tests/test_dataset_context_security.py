import sqlite3

import pytest

from vanna.capabilities.sql_runner import RunSqlToolArgs
from vanna.core.tool import ToolContext
from vanna.core.user import User
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools.run_sql import RunSqlTool


def _context(**metadata: str) -> ToolContext:
    return ToolContext(
        user=User(id="test", username="test"),
        conversation_id="conversation",
        request_id="request",
        agent_memory=DemoAgentMemory(max_items=10),
        metadata=metadata,
    )


def test_selected_version_rewrites_only_authorized_table() -> None:
    args = RunSqlTool._apply_dataset_context(
        RunSqlToolArgs(sql="SELECT * FROM Customer"),
        _context(dataset_id="Customer", resolved_table="_vanna_customer_v1"),
    )

    assert args.sql == 'SELECT * FROM "_vanna_customer_v1"'


def test_selected_version_rejects_other_table_references() -> None:
    with pytest.raises(ValueError, match="outside the selected dataset"):
        RunSqlTool._apply_dataset_context(
            RunSqlToolArgs(sql="SELECT * FROM Customer JOIN Invoice ON 1 = 1"),
            _context(dataset_id="Customer", resolved_table="_vanna_customer_v1"),
        )


def test_sql_tool_accepts_one_read_only_select() -> None:
    RunSqlTool._validate_read_only_sql("WITH recent AS (SELECT 1) SELECT * FROM recent")


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO Customer VALUES (1)",
        "UPDATE Customer SET FirstName = 'x'",
        "DELETE FROM Customer",
        "SELECT 1; DELETE FROM Customer",
    ],
)
def test_sql_tool_rejects_writes_and_multiple_statements(sql: str) -> None:
    with pytest.raises(ValueError, match="read-only"):
        RunSqlTool._validate_read_only_sql(sql)


@pytest.mark.asyncio
async def test_sql_execution_uses_selected_version(tmp_path) -> None:
    database_path = tmp_path / "selected.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE Customer (value INTEGER)")
        connection.execute("CREATE TABLE _vanna_customer_v1 (value INTEGER)")
        connection.execute("INSERT INTO Customer VALUES (1)")
        connection.execute("INSERT INTO _vanna_customer_v1 VALUES (99)")

    tool = RunSqlTool(sql_runner=SqliteRunner(str(database_path)))
    result = await tool.execute(
        _context(dataset_id="Customer", resolved_table="_vanna_customer_v1"),
        RunSqlToolArgs(sql="SELECT value FROM Customer"),
    )

    assert result.success
    assert result.metadata["results"] == [{"value": 99}]
