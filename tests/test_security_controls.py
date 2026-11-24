import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from vanna.examples.mock_quickstart import create_demo_agent
from vanna.servers.base.auth import sign_session
from vanna.servers.fastapi.app import VannaFastAPIServer


SECRET = "test-auth-secret-with-at-least-32-characters"


def _client(database_path: Path) -> TestClient:
    app = VannaFastAPIServer(
        create_demo_agent(),
        config={
            "data_quality_database_path": str(database_path),
            "require_auth": True,
            "auth_secret": SECRET,
            "admin_email": "admin@example.com",
        },
    ).create_app()
    return TestClient(app)


def test_data_quality_requires_signed_authentication(tmp_path: Path) -> None:
    with _client(tmp_path / "secure.sqlite") as client:
        assert client.get("/api/data-quality/datasets").status_code == 401
        client.cookies.set("vanna_email", "admin@example.com")
        assert client.get("/api/data-quality/datasets").status_code == 401


def test_uploaded_dataset_is_owned_by_authenticated_user(tmp_path: Path) -> None:
    database_path = tmp_path / "owned.sqlite"
    owner_cookie = sign_session("owner@example.com", SECRET)
    other_cookie = sign_session("other@example.com", SECRET)
    with _client(database_path) as client:
        client.cookies.set("vanna_session", owner_cookie)
        upload = client.post(
            "/api/data-quality/datasets/upload",
            files={"file": ("owned.csv", b"value\n1\n", "text/csv")},
        )
        assert upload.status_code == 201
        dataset_id = upload.json()["dataset_id"]

        client.cookies.set("vanna_session", other_cookie)
        assert client.get("/api/data-quality/datasets").json()["datasets"] == []
        assert client.post(
            "/api/data-quality/profile",
            json={"dataset_id": dataset_id},
        ).status_code == 404

        client.cookies.set("vanna_session", owner_cookie)
        assert client.post(
            "/api/data-quality/profile",
            json={"dataset_id": dataset_id},
        ).status_code == 200


def test_admin_can_access_owned_dataset_and_legacy_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "admin.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE legacy (value INTEGER)")
        connection.execute("INSERT INTO legacy VALUES (1)")

    with _client(database_path) as client:
        client.cookies.set(
            "vanna_session", sign_session("admin@example.com", SECRET)
        )
        datasets = client.get("/api/data-quality/datasets").json()["datasets"]
        assert any(item["dataset_id"] == "legacy" for item in datasets)


def test_secure_admin_endpoint_rejects_forged_email_cookie(tmp_path: Path) -> None:
    with _client(tmp_path / "admin-config.sqlite") as client:
        client.cookies.set("vanna_email", "admin@example.com")
        response = client.post(
            "/api/vanna/v2/configure/gemini",
            json={"api_key": "not-a-real-key", "model": "gemini-2.5-flash"},
        )
        assert response.status_code == 401
