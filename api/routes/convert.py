import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.schemas.task import ConvertRequest, TaskResponse
from api.services.task_manager import (
    create_task,
    get_task,
    list_tasks,
    delete_task,
    run_convert_task,
)

router = APIRouter()


@router.post("/convert", response_model=TaskResponse)
async def start_convert(req: ConvertRequest):
    uploads_dir = Path("uploads") / req.file_id
    pdf_path = uploads_dir / "input.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在，请先上传")

    file_name = req.file_id + ".pdf"
    task = create_task(req, file_name)
    asyncio.create_task(run_convert_task(task.id, req))
    return task


@router.get("/tasks", response_model=list[TaskResponse])
async def get_tasks():
    return list_tasks()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_detail(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.delete("/tasks/{task_id}")
async def remove_task(task_id: str):
    task = delete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"detail": "已删除"}


@router.get("/tasks/{task_id}/download")
async def download_result(task_id: str):
    uploads_dir = Path("uploads") / task_id
    for suffix in [".md", ".docx"]:
        output = uploads_dir / f"output{suffix}"
        if output.exists():
            media_type = (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                if suffix == ".docx"
                else "text/markdown"
            )
            return FileResponse(path=str(output), filename=f"result{suffix}", media_type=media_type)
    raise HTTPException(status_code=404, detail="结果文件不存在")


@router.get("/tasks/{task_id}/preview")
async def preview_result(task_id: str):
    output = Path("uploads") / task_id / "output.md"
    if not output.exists():
        raise HTTPException(status_code=404, detail="Markdown 预览不可用")
    content = output.read_text(encoding="utf-8")
    return {"content": content}
