from pathlib import Path

from fastapi.testclient import TestClient

from vanna.examples.mock_quickstart import create_demo_agent
from vanna.servers.fastapi.app import VannaFastAPIServer


def test_demo_sales_workflow(tmp_path: Path) -> None:
    database_path = tmp_path / "demo.sqlite"
    app = VannaFastAPIServer(
        create_demo_agent(),
        config={"data_quality_database_path": str(database_path)},
    ).create_app()
    csv_path = (
        Path(__file__).parents[1] / "examples" / "demo_sales.csv"
    )

    with TestClient(app) as client:
        upload = client.post(
            "/api/data-quality/datasets/upload",
            files={"file": (csv_path.name, csv_path.read_bytes(), "text/csv")},
        )
        assert upload.status_code == 201
        dataset_id = upload.json()["dataset_id"]

        assert client.post(
            "/api/data-quality/datasets/preview",
            json={"dataset_id": dataset_id},
        ).status_code == 200
        profile = client.post(
            "/api/data-quality/profile",
            json={"dataset_id": dataset_id},
        ).json()
        assert profile["summary"]["missing_cell_count"] > 0
        assert profile["summary"]["duplicate_row_count"] > 0

        recommendations = client.post(
            "/api/data-quality/recommendations",
            json={"dataset_id": dataset_id},
        ).json()["recommendations"]
        actions = [
            {"action": item["action"], "column": item.get("column")}
            for item in recommendations
            if item["action"] in {"remove_exact_duplicates", "median_imputation"}
        ]
        assert actions

        preview = client.post(
            "/api/data-quality/clean/preview",
            json={"dataset_id": dataset_id, "actions": actions},
        )
        assert preview.status_code == 200
        assert preview.json()["quality_after"]["summary"]["missing_cell_count"] <= (
            preview.json()["quality_before"]["summary"]["missing_cell_count"]
        )

        execution = client.post(
            "/api/data-quality/clean/execute",
            json={"dataset_id": dataset_id, "actions": actions, "approved": True},
        )
        assert execution.status_code == 200
        version_id = execution.json()["version_id"]

        versions = client.get(
            f"/api/data-quality/versions/{dataset_id}"
        ).json()["versions"]
        assert len(versions) == 2
        assert any(item["version_id"] == version_id for item in versions)

        rollback = client.post(
            "/api/data-quality/rollback",
            json={"dataset_id": dataset_id, "version_id": dataset_id},
        )
        assert rollback.status_code == 200
