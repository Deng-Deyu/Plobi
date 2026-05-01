"""
文件导出 API 端点
Phase 3: 任务输出到 workspace/exports/

提供文件导出、列表、删除功能。
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from exports.manager import export_manager

router = APIRouter(prefix="/exports", tags=["exports"])


# ─── Pydantic Models ──────────────────────────────────────

class ExportFileRequest(BaseModel):
    agent_id: str
    task_id: str
    source_path: str
    description: str = ""
    duplicate: bool = True


class ExportContentRequest(BaseModel):
    agent_id: str
    task_id: str
    content: str
    filename: str
    description: str = ""


# ─── Endpoints ────────────────────────────────────────────

@router.get("/files")
async def list_files(agent_id: Optional[str] = None):
    """列出导出的文件"""
    files = export_manager.list_files(agent_id=agent_id)
    return [f.__dict__ for f in files]


@router.get("/files/{file_id}")
async def get_file(file_id: str):
    """获取单个文件信息"""
    file_info = export_manager.get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    return file_info.__dict__


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """删除导出的文件"""
    success = export_manager.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "ok", "deleted": file_id}


@router.post("/export/file")
async def export_file(body: ExportFileRequest):
    """导出文件到 workspace/exports/"""
    try:
        exported = export_manager.export_file(
            agent_id=body.agent_id,
            task_id=body.task_id,
            source_path=body.source_path,
            description=body.description,
            copy=body.copy
        )
        return exported.__dict__
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/content")
async def export_content(body: ExportContentRequest):
    """导出文本内容到文件"""
    try:
        exported = export_manager.export_content(
            agent_id=body.agent_id,
            task_id=body.task_id,
            content=body.content,
            filename=body.filename,
            description=body.description
        )
        return exported.__dict__
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """下载导出的文件"""
    file_info = export_manager.get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(file_info.absolute_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=file_info.filename,
        media_type=file_info.mime_type
    )
