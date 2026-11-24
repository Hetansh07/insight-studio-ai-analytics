import sqlite3
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from vanna.examples.mock_quickstart import create_demo_agent
from vanna.servers.fastapi.app import VannaFastAPIServer


def _client(database_path: Path) -> TestClient:
    app = VannaFastAPIServer(
        create_demo_agent(),
        config={"data_quality_database_path": str(database_path)},
    ).create_app()
    return TestClient(app)


def test_upload_list_preview_and_profile_csv(tmp_path: Path) -> None:
    database_path = tmp_path / "ingestion.sqlite"
    with _client(database_path) as client:
        response = client.post(
            "/api/data-quality/datasets/upload",
            files={
                "file": (
                    "sales.csv",
                    b"region,amount\nNorth,10\nSouth,20\n",
                    "text/csv",
                )
            },
        )

        assert response.status_code == 201
        metadata = response.json()
        dataset_id = metadata["dataset_id"]
        assert metadata["original_filename"] == "sales.csv"
        assert metadata["row_count"] == 2
        assert Path(metadata["original_path"]).read_bytes() == (
            b"region,amount\nNorth,10\nSouth,20\n"
        )

        listed = client.get("/api/data-quality/datasets")
        assert listed.status_code == 200
        assert any(item["dataset_id"] == dataset_id for item in listed.json()["datasets"])

        preview = client.post(
            "/api/data-quality/datasets/preview",
            json={"dataset_id": dataset_id, "limit": 1},
        )
        assert preview.status_code == 200
        assert preview.json()["rows"] == [{"region": "North", "amount": 10}]

        profile = client.post(
            "/api/data-quality/profile",
            json={"dataset_id": dataset_id},
        )
        assert profile.status_code == 200
        assert profile.json()["summary"]["row_count"] == 2


def test_upload_rejects_unsafe_filename_and_extension(tmp_path: Path) -> None:
    with _client(tmp_path / "ingestion.sqlite") as client:
        traversal = client.post(
            "/api/data-quality/datasets/upload",
            files={"file": ("..\\outside.csv", b"a\n1\n", "text/csv")},
        )
        unsupported = client.post(
            "/api/data-quality/datasets/upload",
            files={"file": ("data.exe", b"not data", "application/octet-stream")},
        )

        assert traversal.status_code == 400
        assert unsupported.status_code == 400


def test_uploaded_dataset_survives_service_reinitialization(tmp_path: Path) -> None:
    database_path = tmp_path / "persistent.sqlite"
    with _client(database_path) as client:
        response = client.post(
            "/api/data-quality/datasets/upload",
            files={"file": ("data.json", b'{"value": [1, 2]}', "application/json")},
        )
        assert response.status_code == 201
        dataset_id = response.json()["dataset_id"]

    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = ?",
            (dataset_id,),
        ).fetchone()[0] == 1

    with _client(database_path) as client:
        assert client.get("/api/data-quality/datasets").status_code == 200


def test_upload_json_and_xlsx_formats(tmp_path: Path) -> None:
    database_path = tmp_path / "formats.sqlite"
    xlsx_buffer = BytesIO()
    pd.DataFrame({"region": ["North"], "amount": [10]}).to_excel(
        xlsx_buffer, index=False, engine="openpyxl"
    )
    with _client(database_path) as client:
        for filename, content, content_type in (
            ("sales.json", b'[{"region":"South","amount":20}]', "application/json"),
            (
                "sales.xlsx",
                xlsx_buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        ):
            response = client.post(
                "/api/data-quality/datasets/upload",
                files={"file": (filename, content, content_type)},
            )
            assert response.status_code == 201
            dataset_id = response.json()["dataset_id"]
            preview = client.post(
                "/api/data-quality/datasets/preview",
                json={"dataset_id": dataset_id},
            )
            assert preview.status_code == 200
            assert preview.json()["row_count"] == 1


def test_chart_data_uses_selected_dataset_and_validates_columns(tmp_path: Path) -> None:
    with _client(tmp_path / "charts.sqlite") as client:
        response = client.post(
            "/api/data-quality/datasets/upload",
            files={
                "file": (
                    "sales.csv",
                    b"region,amount\nNorth,10\nNorth,15\nSouth,20\n",
                    "text/csv",
                )
            },
        )
        dataset_id = response.json()["dataset_id"]

        chart = client.post(
            "/api/data-quality/chart-data",
            json={
                "dataset_id": dataset_id,
                "version_id": dataset_id,
                "chart_type": "bar",
                "x_column": "region",
                "y_column": "amount",
                "aggregation": "sum",
                "sort_order": "descending",
                "limit": 10,
            },
        )
        assert chart.status_code == 200
        assert chart.json()["traces"][0]["x"] == ["North", "South"]
        assert chart.json()["traces"][0]["y"] == [25, 20]
        assert any(column["name"] == "amount" and column["numeric"] for column in chart.json()["columns"])

        invalid = client.post(
            "/api/data-quality/chart-data",
            json={
                "dataset_id": dataset_id,
                "chart_type": "bar",
                "x_column": "missing",
                "y_column": "amount",
            },
        )
        assert invalid.status_code == 400
