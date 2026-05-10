import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

UPLOADS_DIR = Path("uploads")


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    file_id = uuid.uuid4().hex[:12]
    task_dir = UPLOADS_DIR / file_id
    task_dir.mkdir(parents=True, exist_ok=True)

    dest = task_dir / "input.pdf"
    content = await file.read()
    dest.write_bytes(content)

    return {"file_id": file_id, "file_name": file.filename, "size": len(content)}
