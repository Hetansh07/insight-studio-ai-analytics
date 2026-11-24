"""
FastAPI route implementations for Vanna Agents.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse, HTMLResponse

from ..base import ChatHandler, ChatRequest, ChatResponse
from ..base.auth import AuthenticatedUser, authenticate_request
from ..base.templates import get_index_html
from ...core.user.request_context import RequestContext
from ...data_quality import CleaningAction, SQLiteDataQualityService

logger = logging.getLogger(__name__)


class DataQualityDatasetRequest(BaseModel):
    dataset_id: str = Field(min_length=1, max_length=128)


class DataQualityPreviewRequest(DataQualityDatasetRequest):
    limit: int = Field(default=20, ge=1, le=1000)


class DataQualityChartRequest(DataQualityDatasetRequest):
    version_id: Optional[str] = Field(default=None, max_length=128)
    chart_type: str = Field(min_length=1, max_length=32)
    x_column: str = Field(min_length=1, max_length=128)
    y_column: Optional[str] = Field(default=None, max_length=128)
    group_by: Optional[str] = Field(default=None, max_length=128)
    aggregation: str = Field(default="sum", max_length=16)
    sort_order: str = Field(default="default", max_length=16)
    limit: int = Field(default=50, ge=1, le=200)


class DataQualityCleaningRequest(DataQualityDatasetRequest):
    actions: List[CleaningAction] = Field(min_length=1)


class DataQualityExecuteRequest(DataQualityCleaningRequest):
    approved: bool


class DataQualityRollbackRequest(DataQualityDatasetRequest):
    version_id: str = Field(min_length=1, max_length=128)


class GeminiConfiguration(BaseModel):
    api_key: str = Field(min_length=1, max_length=512)
    model: str = Field(default="gemini-3.5-flash-lite", min_length=1, max_length=100)


def register_chat_routes(
    app: FastAPI, chat_handler: ChatHandler, config: Optional[Dict[str, Any]] = None
) -> None:
    """Register chat routes on FastAPI app.

    Args:
        app: FastAPI application
        chat_handler: Chat handler instance
        config: Server configuration
    """
    config = config or {}

    def data_quality_service() -> SQLiteDataQualityService:
        service = config.get("data_quality_service")
        if not isinstance(service, SQLiteDataQualityService):
            raise HTTPException(
                status_code=503,
                detail="Data quality is not configured for this server",
            )
        return service

    def authorized_service(
        request: Request, dataset_id: Optional[str] = None
    ) -> tuple[SQLiteDataQualityService, AuthenticatedUser]:
        user = authenticate_request(request, config)
        service = data_quality_service()
        if dataset_id:
            try:
                service.authorize(dataset_id, user.user_id, user.is_admin)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        return service, user

    @app.get("/api/data-quality/datasets")
    async def list_datasets(request: Request) -> Dict[str, Any]:
        service, user = authorized_service(request)
        return {
            "datasets": service.list_datasets(user.user_id, user.is_admin)
        }

    @app.post("/api/data-quality/datasets/upload", status_code=201)
    async def upload_dataset(
        request: Request, file: UploadFile = File(...)
    ) -> Dict[str, Any]:
        try:
            service, user = authorized_service(request)
            content = await file.read(
                int(config.get("max_upload_bytes", 10 * 1024 * 1024)) + 1
            )
            return service.upload(
                file.filename or "", content,
                owner_id=user.user_id,
                max_bytes=int(config.get("max_upload_bytes", 10 * 1024 * 1024)),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/data-quality/datasets/preview")
    async def preview_dataset(
        request: DataQualityPreviewRequest, http_request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(http_request, request.dataset_id)
            return service.dataset_preview(
                request.dataset_id, request.limit
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/data-quality/chart-data")
    async def chart_data(
        request: DataQualityChartRequest, http_request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(http_request, request.dataset_id)
            return service.chart_data(
                request.dataset_id, request.version_id, request.chart_type,
                request.x_column, request.y_column, request.group_by,
                request.aggregation, request.sort_order, request.limit,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/data-quality/profile")
    async def profile_table(
        request: DataQualityDatasetRequest, http_request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(http_request, request.dataset_id)
            return service.profile(request.dataset_id).model_dump()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/data-quality/profile/{dataset_id}")
    async def get_profile(dataset_id: str, request: Request) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(request, dataset_id)
            return service.profile(dataset_id).model_dump()
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/data-quality/recommendations")
    async def get_recommendations(
        request: DataQualityDatasetRequest, http_request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(http_request, request.dataset_id)
            recommendations = service.recommendations(
                request.dataset_id
            )
            return {"dataset_id": request.dataset_id, "recommendations": [
                item.model_dump() for item in recommendations
            ]}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/data-quality/clean/preview")
    async def preview_cleaning(
        request: DataQualityCleaningRequest, http_request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(http_request, request.dataset_id)
            return service.preview(
                request.dataset_id, request.actions
            )
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/data-quality/clean/execute")
    async def execute_cleaning(
        request: DataQualityExecuteRequest, http_request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(http_request, request.dataset_id)
            return service.execute(
                request.dataset_id, request.actions, request.approved
            )
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/data-quality/history/{dataset_id}")
    async def get_cleaning_history(
        dataset_id: str, request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(request, dataset_id)
            return {"dataset_id": dataset_id, "history": service.history(dataset_id)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/data-quality/versions/{dataset_id}")
    async def get_dataset_versions(
        dataset_id: str, request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(request, dataset_id)
            return {"dataset_id": dataset_id, "versions": service.versions(dataset_id)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/data-quality/rollback")
    async def rollback_cleaning(
        request: DataQualityRollbackRequest, http_request: Request
    ) -> Dict[str, Any]:
        try:
            service, _ = authorized_service(http_request, request.dataset_id)
            return service.rollback(
                request.dataset_id, request.version_id
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        """Serve the main chat interface."""
        dev_mode = config.get("dev_mode", False)
        cdn_url = config.get("cdn_url", "https://img.vanna.ai/vanna-components.js")
        api_base_url = config.get("api_base_url", "")

        return get_index_html(
            dev_mode=dev_mode, cdn_url=cdn_url, api_base_url=api_base_url
        )

    @app.post("/api/vanna/v2/configure/gemini")
    async def configure_gemini(
        configuration: GeminiConfiguration, http_request: Request
    ) -> Dict[str, str]:
        """Configure Gemini in memory for the current server process."""
        user = authenticate_request(http_request, config)
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin login required")

        try:
            from ...integrations.google import GeminiLlmService

            chat_handler.agent.llm_service = GeminiLlmService(
                api_key=configuration.api_key,
                model=configuration.model,
            )
        except (ImportError, ValueError) as exc:
            logger.exception("Gemini configuration failed")
            raise HTTPException(
                status_code=400, detail="Gemini configuration failed"
            ) from exc

        return {"status": "configured", "provider": "google-gemini"}

    @app.post("/api/vanna/v2/chat_sse")
    async def chat_sse(
        chat_request: ChatRequest, http_request: Request
    ) -> StreamingResponse:
        """Server-Sent Events endpoint for streaming chat."""
        # Extract request context for user resolution
        chat_request.request_context = RequestContext(
            cookies=dict(http_request.cookies),
            headers=dict(http_request.headers),
            remote_addr=http_request.client.host if http_request.client else None,
            query_params=dict(http_request.query_params),
            metadata=chat_request.metadata,
        )
        _resolve_chat_dataset(chat_request, http_request)

        async def generate() -> AsyncGenerator[str, None]:
            """Generate SSE stream."""
            try:
                async for chunk in chat_handler.handle_stream(chat_request):
                    chunk_json = chunk.model_dump_json()
                    yield f"data: {chunk_json}\n\n"
                yield "data: [DONE]\n\n"
            except Exception:
                logger.exception("Chat stream failed")
                error_data = {
                    "type": "error",
                    "data": {"message": "The request could not be completed."},
                    "conversation_id": chat_request.conversation_id or "",
                    "request_id": chat_request.request_id or "",
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    @app.websocket("/api/vanna/v2/chat_websocket")
    async def chat_websocket(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time chat."""
        await websocket.accept()

        try:
            while True:
                # Receive message
                try:
                    data = await websocket.receive_json()

                    # Extract request context for user resolution
                    metadata = data.get("metadata", {})
                    data["request_context"] = RequestContext(
                        cookies=dict(websocket.cookies),
                        headers=dict(websocket.headers),
                        remote_addr=websocket.client.host if websocket.client else None,
                        query_params=dict(websocket.query_params),
                        metadata=metadata,
                    )

                    chat_request = ChatRequest(**data)
                    _resolve_chat_dataset(chat_request, websocket)
                except Exception:
                    logger.exception("Invalid websocket chat request")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "data": {"message": "Invalid chat request."},
                        }
                    )
                    continue

                # Stream response
                try:
                    async for chunk in chat_handler.handle_stream(chat_request):
                        await websocket.send_json(chunk.model_dump())

                    # Send completion signal
                    await websocket.send_json(
                        {
                            "type": "completion",
                            "data": {"status": "done"},
                            "conversation_id": chunk.conversation_id
                            if "chunk" in locals()
                            else "",
                            "request_id": chunk.request_id
                            if "chunk" in locals()
                            else "",
                        }
                    )

                except Exception:
                    logger.exception("Websocket chat stream failed")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "data": {"message": "The request could not be completed."},
                            "conversation_id": chat_request.conversation_id or "",
                            "request_id": chat_request.request_id or "",
                        }
                    )

        except WebSocketDisconnect:
            pass
        except Exception:
            logger.exception("Websocket connection failed")
            try:
                await websocket.send_json(
                    {
                        "type": "error",
                        "data": {"message": "The websocket request failed."},
                    }
                )
            except Exception:
                pass
            finally:
                await websocket.close()

    @app.post("/api/vanna/v2/chat_poll")
    async def chat_poll(
        chat_request: ChatRequest, http_request: Request
    ) -> ChatResponse:
        """Polling endpoint for chat."""
        # Extract request context for user resolution
        chat_request.request_context = RequestContext(
            cookies=dict(http_request.cookies),
            headers=dict(http_request.headers),
            remote_addr=http_request.client.host if http_request.client else None,
            query_params=dict(http_request.query_params),
            metadata=chat_request.metadata,
        )
        _resolve_chat_dataset(chat_request, http_request)

        try:
            result = await chat_handler.handle_poll(chat_request)
            return result
        except Exception:
            logger.exception("Chat polling failed")
            raise HTTPException(
                status_code=500, detail="The request could not be completed."
            )

    def _resolve_chat_dataset(chat_request: ChatRequest, request: Request) -> None:
        """Validate and attach trusted dataset context to this request only."""
        selected_dataset = chat_request.metadata.get("dataset_id")
        selected_version = chat_request.metadata.get("version_id")
        if not selected_dataset:
            return
        service = data_quality_service()
        user = authenticate_request(request, config)
        try:
            service.authorize(str(selected_dataset), user.user_id, user.is_admin)
            resolved_table = service.resolve_version(
                str(selected_dataset),
                str(selected_version) if selected_version else None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        chat_request.metadata["resolved_table"] = resolved_table
        chat_request.request_context.metadata.update(
            {
                "dataset_id": str(selected_dataset),
                "version_id": str(selected_version or selected_dataset),
                "resolved_table": resolved_table,
            }
        )
