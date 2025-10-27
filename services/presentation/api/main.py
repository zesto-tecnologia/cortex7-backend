from typing import Annotated, Optional
import uuid
from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from services.presentation.api.lifespan import app_lifespan
from services.presentation.api.middlewares import UserConfigEnvUpdateMiddleware
from services.presentation.api.v1.ppt.router import API_V1_PPT_ROUTER
from services.presentation.api.v1.webhook.router import API_V1_WEBHOOK_ROUTER
from services.presentation.api.v1.mock.router import API_V1_MOCK_ROUTER
from services.presentation.services.database import get_async_session
from services.presentation.models.sql.presentation import PresentationModel
from services.presentation.utils.export_utils import export_presentation
from services.presentation.utils.get_env import get_app_data_directory_env
import os


class ExportPdfRequest(BaseModel):
    id: str
    title: Optional[str] = None


app = FastAPI(lifespan=app_lifespan)


# Routers
app.include_router(API_V1_PPT_ROUTER)
app.include_router(API_V1_WEBHOOK_ROUTER)
app.include_router(API_V1_MOCK_ROUTER)

# Middlewares
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(UserConfigEnvUpdateMiddleware)


# Direct API endpoints (for frontend compatibility)
@app.post("/api/export-as-pdf")
async def export_as_pdf_endpoint(
    request: ExportPdfRequest,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Export presentation as PDF - endpoint compatible with frontend."""
    try:
        presentation_id = uuid.UUID(request.id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid presentation ID format")

    presentation = await sql_session.get(PresentationModel, presentation_id)

    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    presentation_title = request.title or presentation.title or str(uuid.uuid4())
    presentation_and_path = await export_presentation(
        presentation_id,
        presentation_title,
        "pdf",
    )

    return {"path": presentation_and_path.path}


# Mount static files for app_data directory (images, exports, etc.)
app_data_dir = get_app_data_directory_env()
if app_data_dir:
    os.makedirs(app_data_dir, exist_ok=True)
    app.mount("/app_data", StaticFiles(directory=app_data_dir), name="app_data")

# Mount static assets (icons, etc.)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
