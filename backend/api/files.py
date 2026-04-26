"""
文件上传 API 端点
Phase 2: 多模态输入
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid
from datetime import datetime

from multimodal.file_processor import FileProcessor

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/files", tags=["files"])
processor = FileProcessor()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件并处理"""
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_name
    
    # 保存文件
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 处理文件
    try:
        processed = await processor.process(str(file_path))
        return {
            "file_id": unique_name,
            "original_name": file.filename,
            "file_path": str(file_path),
            "processed": processed,
            "uploaded_at": datetime.now().isoformat()
        }
    except Exception as e:
        # 处理失败也返回文件信息
        return {
            "file_id": unique_name,
            "original_name": file.filename,
            "file_path": str(file_path),
            "error": f"文件处理失败: {str(e)}",
            "uploaded_at": datetime.now().isoformat()
        }


@router.get("/list")
async def list_files():
    """列出所有上传的文件"""
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "file_id": file_path.name,
                "file_path": str(file_path),
                "size": file_path.stat().st_size,
                "uploaded_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    return {"files": files}


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """删除文件"""
    file_path = UPLOAD_DIR / file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        file_path.unlink()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")
