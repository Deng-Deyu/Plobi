"""
文档处理器
Phase 2: 多模态输入
"""

from pathlib import Path

from multimodal.types import ProcessedFile


class DocHandler:
    """文档处理器（PDF、Word、Markdown）"""
    
    async def process_pdf(self, file_path: str) -> ProcessedFile:
        """处理 PDF 文件"""
        path = Path(file_path)
        
        # Phase 2: 简化版，只返回基本信息
        # Phase 3: 集成 PyMuPDF 提取文字和图片
        
        return ProcessedFile(
            type="document",
            content=f"[PDF 文档: {path.name}]",
            images=[],
            metadata={
                "size": path.stat().st_size,
                "format": "pdf",
                "pages": 0  # 需要 PyMuPDF 获取
            }
        )
    
    async def process_docx(self, file_path: str) -> ProcessedFile:
        """处理 Word 文档"""
        path = Path(file_path)
        
        # Phase 2: 简化版，只返回基本信息
        # Phase 3: 集成 python-docx 提取内容
        
        return ProcessedFile(
            type="document",
            content=f"[Word 文档: {path.name}]",
            images=[],
            metadata={
                "size": path.stat().st_size,
                "format": "docx"
            }
        )
