import asyncio
import uuid
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from api.schemas.task import (
    ConvertRequest,
    TaskResponse,
    TaskProgress,
    TaskStatusEnum,
    TaskPhase,
)
from api.services.progress import broadcaster
from config_manager import ConfigManager
from config_defaults import build_config_for_profile


tasks: Dict[str, TaskResponse] = {}


def create_task(req: ConvertRequest, file_name: str) -> TaskResponse:
    task_id = req.file_id
    task = TaskResponse(
        id=task_id,
        file_name=file_name,
        output_format=req.output_format,
        mode=req.mode if req.output_format == "word" else None,
        status=TaskStatusEnum.pending,
        created_at=datetime.now(),
    )
    tasks[task_id] = task
    return task


def get_task(task_id: str):
    return tasks.get(task_id)


def list_tasks():
    return list(tasks.values())


def delete_task(task_id: str):
    return tasks.pop(task_id, None)


def _make_progress_callback(task_id: str, task: TaskResponse, loop: asyncio.AbstractEventLoop):
    def callback(event: dict):
        task.progress.current_page = event.get("current_page", task.progress.current_page)
        task.progress.total_pages = event.get("total_pages", task.progress.total_pages)
        task.progress.cached_pages = event.get("cached_pages", task.progress.cached_pages)
        task.progress.failed_pages = event.get("failed_pages", task.progress.failed_pages)
        task.progress.message = event.get("message", "")

        phase_str = event.get("phase", "processing")
        try:
            task.progress.phase = TaskPhase(phase_str)
        except ValueError:
            task.progress.phase = TaskPhase.processing

        broadcast_data = {
            "phase": phase_str,
            "current_page": task.progress.current_page,
            "total_pages": task.progress.total_pages,
            "cached_pages": task.progress.cached_pages,
            "failed_pages": task.progress.failed_pages,
            "message": task.progress.message,
        }
        asyncio.run_coroutine_threadsafe(
            broadcaster.broadcast(task_id, "progress", broadcast_data),
            loop,
        )
    return callback


async def run_convert_task(task_id: str, req: ConvertRequest):
    task = tasks.get(task_id)
    if not task:
        return

    task.status = TaskStatusEnum.processing
    task.progress.phase = TaskPhase.processing
    task.progress.message = "转换中..."
    await broadcaster.broadcast(task_id, "progress", {"phase": "processing", "message": "转换中...", "current_page": 0, "total_pages": 0, "cached_pages": 0, "failed_pages": []})

    uploads_dir = Path("uploads") / task_id
    pdf_path = str(uploads_dir / "input.pdf")
    suffix = ".docx" if req.output_format == "word" else ".md"
    output_path = str(uploads_dir / f"output{suffix}")

    cm = ConfigManager()
    profiles = cm.list_profiles()
    if not profiles:
        task.status = TaskStatusEnum.failed
        task.error = "未配置 API profile，请先在设置中创建配置"
        task.completed_at = datetime.now()
        await broadcaster.broadcast(task_id, "error", {"message": task.error})
        return

    last_profile = cm.get_last_profile()
    if last_profile is None:
        last_profile = cm.get_profile(profiles[0])

    config = build_config_for_profile(last_profile)

    import yaml
    with open("config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    loop = asyncio.get_event_loop()
    progress_callback = _make_progress_callback(task_id, task, loop)

    try:
        if req.output_format == "word":
            from main_word import main as word_main
            await asyncio.to_thread(word_main, pdf_path, output_path, req.mode, req.resume, progress_callback)
        else:
            from main import main as md_main
            await asyncio.to_thread(md_main, pdf_path, output_path, req.resume, progress_callback)

        task.status = TaskStatusEnum.completed
        task.progress.phase = TaskPhase.done
        task.progress.message = "转换完成"
        task.completed_at = datetime.now()
        await broadcaster.broadcast(task_id, "completed", {"message": "转换完成"})
    except Exception as e:
        task.status = TaskStatusEnum.failed
        task.error = str(e)
        task.completed_at = datetime.now()
        await broadcaster.broadcast(task_id, "error", {"message": str(e)})
