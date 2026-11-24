"""ClickHouse implementation of SqlRunner interface."""

from typing import Optional
import pandas as pd

from vanna.capabilities.sql_runner import SqlRunner, RunSqlToolArgs
from vanna.core.tool import ToolContext


class ClickHouseRunner(SqlRunner):
    """ClickHouse implementation of the SqlRunner interface."""

    def __init__(
        self,
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 8123,
        **kwargs,
    ):
        """Initialize with ClickHouse connection parameters.

        Args:
            host: Database host address
            database: Database name
            user: Database user
            password: Database password
            port: Database port (default: 8123)
            **kwargs: Additional clickhouse_connect connection parameters
        """
        try:
            import clickhouse_connect
        except ImportError:
            self.clickhouse_connect = None
        else:
            self.clickhouse_connect = clickhouse_connect

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.kwargs = kwargs

    async def run_sql(self, args: RunSqlToolArgs, context: ToolContext) -> pd.DataFrame:
        """Execute SQL query against ClickHouse database and return results as DataFrame.

        Args:
            args: SQL query arguments
            context: Tool execution context

        Returns:
            DataFrame with query results

        Raises:
            Exception: If query execution fails
        """
        if self.clickhouse_connect is None:
            raise ImportError(
                "clickhouse-connect package is required. "
                "Install with: pip install 'vanna[clickhouse]'"
            )

        client = self.clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=self.database,
            **self.kwargs,
        )

        try:
            result = client.query(args.sql)
            results = result.result_rows
            df = pd.DataFrame(results, columns=result.column_names)
            return df
        finally:
            client.close()
