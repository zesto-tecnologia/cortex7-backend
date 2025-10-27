from typing import Annotated, List
from fastapi import APIRouter, Body, HTTPException

from services.presentation.utils.available_models import list_available_anthropic_models

ANTHROPIC_ROUTER = APIRouter(prefix="/anthropic", tags=["Anthropic"])


@ANTHROPIC_ROUTER.post("/models/available", response_model=List[str])
async def get_available_models(
    api_key: Annotated[str, Body(embed=True)],
):
    try:
        return await list_available_anthropic_models(api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
