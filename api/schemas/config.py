from typing import Optional
from pydantic import BaseModel


class ProfileCreate(BaseModel):
    name: str
    api_url: str
    api_key: str
    model: str
    dpi: int = 150
    chunk_size: int = 10


class ProfileResponse(BaseModel):
    name: str
    api_url: str
    model: str
    dpi: int = 150
    chunk_size: int = 10
