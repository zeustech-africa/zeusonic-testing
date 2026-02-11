from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

MUREKA_API_KEY = os.getenv("MUREKA_API_KEY")
MUREKA_BASE_URL = "https://api.mureka.ai/v1"


class TransformRequest(BaseModel):
    audio_url: str
    style: str
    instruments: list[str] = []


async def call_mureka(endpoint: str, payload: dict):
    if not MUREKA_API_KEY:
        raise HTTPException(status_code=500, detail="Missing MUREKA_API_KEY")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{MUREKA_BASE_URL}/{endpoint}",
            headers={
                "Authorization": f"Bearer {MUREKA_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=response.text)

    return response.json()


@router.post("/transform")
async def transform_audio(payload: TransformRequest):
    return await call_mureka(
        "transform",
        {
            "audio_url": payload.audio_url,
            "target_style": payload.style,
            "additional_instruments": payload.instruments,
            "separate_stems": True,
        },
    )


@router.post("/separate")
async def separate_audio(payload: dict):
    """
    Splits uploaded audio into:
    - vocals
    - instrumental
    Uses Mureka stem separation.
    """
    return await call_mureka("separate", payload)


@router.post("/mix")
async def ai_mix(payload: dict):
    """
    Mix vocals + beat + added instruments.
    AI handles blending + mastering.
    """
    return await call_mureka("mix", payload)


@router.post("/add-instrument")
async def add_instrument(payload: dict):
    """
    Add AI-generated instrument layer.
    """
    return await call_mureka("add_instrument", payload)


@router.post("/vocal-style")
async def vocal_style(payload: dict):
    """
    Modify vocal tone / texture / energy.
    """
    return await call_mureka("vocal_style", payload)


@router.post("/master")
async def master_track(payload: dict):
    """
    Final mastering stage.
    """
    return await call_mureka("master", payload)
