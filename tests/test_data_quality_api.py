"""API tests for the SQLite-backed data quality workflow."""

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from vanna.examples.mock_quickstart import create_demo_agent
from vanna.servers.fastapi.app import VannaFastAPIServer


def test_data_quality_api_preserves_original_and_versions_database(tmp_path: Path) -> None:
    database_path = tmp_path / "quality.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE sales (category TEXT, amount REAL)")
        connection.executemany(
            "INSERT INTO sales VALUES (?, ?)",
            [("A", 10.0), ("A", 10.0), ("B", None)],
        )

    app = VannaFastAPIServer(
        create_demo_agent(),
        config={"data_quality_database_path": str(database_path)},
    ).create_app()

    with TestClient(app) as client:
        profile = client.post(
            "/api/data-quality/profile", json={"dataset_id": "sales"}
        )
        assert profile.status_code == 200
        assert profile.json()["summary"]["duplicate_row_count"] == 1

        recommendations = client.post(
            "/api/data-quality/recommendations",
            json={"dataset_id": "sales"},
        )
        assert recommendations.status_code == 200
        assert recommendations.json()["recommendations"]

        actions = [
            {"action": "remove_exact_duplicates"},
            {"action": "median_imputation", "column": "amount"},
        ]
        preview = client.post(
            "/api/data-quality/clean/preview",
            json={"dataset_id": "sales", "actions": actions},
        )
        assert preview.status_code == 200
        assert preview.json()["preview"]["after_rows"] == 2

        execution = client.post(
            "/api/data-quality/clean/execute",
            json={"dataset_id": "sales", "actions": actions, "approved": True},
        )
        assert execution.status_code == 200
        version_id = execution.json()["version_id"]

        history = client.get("/api/data-quality/history/sales")
        assert history.status_code == 200
        assert len(history.json()["history"]) == 1

        versions = client.get("/api/data-quality/versions/sales")
        assert versions.status_code == 200
        assert len(versions.json()["versions"]) == 2

        rollback = client.post(
            "/api/data-quality/rollback",
            json={"dataset_id": "sales", "version_id": version_id},
        )
        assert rollback.status_code == 200

        invalid_chat = client.post(
            "/api/vanna/v2/chat_sse",
            json={
                "message": "What is the total?",
                "metadata": {
                    "dataset_id": "sales",
                    "version_id": "_vanna_other_v1",
                },
            },
        )
        assert invalid_chat.status_code == 400

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 3
