"""Tool for profiling a permitted database table through the existing SQL runner."""

import re
from typing import Any, Dict, Type

from pydantic import BaseModel, Field

from vanna.capabilities.sql_runner import RunSqlToolArgs, SqlRunner
from vanna.components import SimpleTextComponent, UiComponent
from vanna.core.tool import Tool, ToolContext, ToolResult
from vanna.data_quality import DataProfiler


class ProfileTableArgs(BaseModel):
    """Arguments for profiling a database table."""

    table_name: str = Field(min_length=1, max_length=128)
    sample_size: int = Field(default=10000, ge=1, le=100000)


class ProfileTableTool(Tool[ProfileTableArgs]):
    """Profile a bounded table sample without changing database contents."""

    def __init__(self, sql_runner: SqlRunner):
        self.sql_runner = sql_runner
        self.profiler = DataProfiler()

    @property
    def name(self) -> str:
        return "profile_table"

    @property
    def description(self) -> str:
        return (
            "Profile a database table for missing values, duplicates, distributions, "
            "outliers, and a transparent quality score. This is read-only."
        )

    def get_args_schema(self) -> Type[ProfileTableArgs]:
        return ProfileTableArgs

    async def execute(
        self, context: ToolContext, args: ProfileTableArgs
    ) -> ToolResult:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.table_name):
            message = "Invalid table name. Use a simple table identifier."
            return ToolResult(
                success=False,
                result_for_llm=message,
                ui_component=UiComponent(
                    simple_component=SimpleTextComponent(text=message)
                ),
                error=message,
            )

        query = f'SELECT * FROM "{args.table_name}" LIMIT {args.sample_size}'
        dataframe = await self.sql_runner.run_sql(
            RunSqlToolArgs(sql=query), context
        )
        report = self.profiler.profile(dataframe)
        payload: Dict[str, Any] = report.model_dump()
        message = (
            f"Profiled table '{args.table_name}' using {report.summary.row_count} "
            f"rows. Overall data quality score: {report.scores.overall}/100. "
            f"Issues: {', '.join(report.issues) if report.issues else 'none'}"
        )
        return ToolResult(
            success=True,
            result_for_llm=f"{message}\nProfile: {payload}",
            ui_component=UiComponent(
                simple_component=SimpleTextComponent(text=message)
            ),
            metadata={"profile": payload, "table_name": args.table_name},
        )
