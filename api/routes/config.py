import sys
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.schemas.config import ProfileCreate, ProfileResponse
from config_manager import ConfigManager

router = APIRouter()


def _get_cm():
    return ConfigManager()


class TestConnectionRequest(BaseModel):
    api_url: str
    api_key: str
    model: str


@router.post("/config/test-connection")
async def test_connection(req: TestConnectionRequest):
    import asyncio
    from openai import OpenAI

    def _test():
        client = OpenAI(api_key=req.api_key, base_url=req.api_url, timeout=15)
        start = time.time()
        client.chat.completions.create(
            model=req.model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
        )
        return int((time.time() - start) * 1000)

    try:
        latency_ms = await asyncio.to_thread(_test)
        return {"success": True, "message": "连接成功", "latency_ms": latency_ms}
    except Exception as e:
        return {"success": False, "message": str(e), "latency_ms": 0}


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
