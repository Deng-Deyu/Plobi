"""
文件统一处理入口
Phase 2: 多模态输入
"""

from pathlib import Path
from typing import Optional
import mimetypes

from multimodal.types import ProcessedFile
from multimodal.image_handler import ImageHandler
from multimodal.audio_handler import AudioHandler
from multimodal.doc_handler import DocHandler
from multimodal.music_handler import MusicHandler


class FileProcessor:
    """统一文件处理入口，根据 MIME 类型路由到专项处理器"""
    
    def __init__(self):
        self.image_handler = ImageHandler()
        self.audio_handler = AudioHandler()
        self.doc_handler = DocHandler()
        self.music_handler = MusicHandler()
    
    async def process(self, file_path: str) -> ProcessedFile:
        """处理文件"""
        path = Path(file_path)
        mime, _ = mimetypes.guess_type(str(path))
        
        if mime and mime.startswith("image/"):
            return await self.image_handler.process(file_path)
        elif mime and mime.startswith("audio/"):
            return await self.audio_handler.process(file_path)
        elif mime == "application/pdf":
            return await self.doc_handler.process_pdf(file_path)
        elif mime in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ):
            return await self.doc_handler.process_docx(file_path)
        elif path.suffix in (".gp", ".gpx", ".gp5"):
            return await self.music_handler.process_guitar_pro(file_path)
        else:
            # 文本类文件
            return self._process_text(file_path)
    
    def _process_text(self, file_path: str) -> ProcessedFile:
        """处理文本文件"""
        path = Path(file_path)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="gbk", errors="replace")
        
        return ProcessedFile(
            type="text",
            content=content,
            images=[],
            metadata={"size": path.stat().st_size}
        )
