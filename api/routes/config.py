import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.schemas.config import ProfileCreate, ProfileResponse
from config_manager import ConfigManager

router = APIRouter()


def _get_cm():
    return ConfigManager()


@router.get("/config/profiles", response_model=list[ProfileResponse])
async def list_profiles():
    cm = _get_cm()
    result = []
    for name in cm.list_profiles():
        profile = cm.get_profile(name)
        if profile:
            result.append(ProfileResponse(
                name=name,
                api_url=profile["api_url"],
                model=profile["model"],
                dpi=profile.get("dpi", 150),
                chunk_size=profile.get("chunk_size", 10),
            ))
    return result


@router.post("/config/profiles", response_model=ProfileResponse)
async def create_profile(req: ProfileCreate):
    cm = _get_cm()
    cm.save_profile(
        name=req.name,
        api_url=req.api_url,
        api_key=req.api_key,
        model=req.model,
        dpi=req.dpi,
        chunk_size=req.chunk_size,
    )
    return ProfileResponse(
        name=req.name,
        api_url=req.api_url,
        model=req.model,
        dpi=req.dpi,
        chunk_size=req.chunk_size,
    )


@router.delete("/config/profiles/{name}")
async def delete_profile(name: str):
    cm = _get_cm()
    if name not in cm.list_profiles():
        raise HTTPException(status_code=404, detail="配置不存在")
    cm.delete_profile(name)
    return {"detail": "已删除"}
