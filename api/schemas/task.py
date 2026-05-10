from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel


class TaskPhase(str, Enum):
    pending = "pending"
    rendering = "rendering"
    processing = "processing"
    writing = "writing"
    done = "done"


class TaskStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ConvertRequest(BaseModel):
    file_id: str
    output_format: str  # "markdown" | "word"
    mode: str = "precise"  # "fast" | "precise"
    resume: bool = False


class TaskProgress(BaseModel):
    current_page: int = 0
    total_pages: int = 0
    cached_pages: int = 0
    failed_pages: List[int] = []
    phase: TaskPhase = TaskPhase.pending
    message: str = ""


class TaskResponse(BaseModel):
    id: str
    file_name: str
    output_format: str
    mode: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.pending
    progress: TaskProgress = TaskProgress()
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
