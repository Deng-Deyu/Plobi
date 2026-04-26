"""
图片处理器
Phase 2: 多模态输入
"""

from pathlib import Path
import base64

from multimodal.types import ProcessedFile


class ImageHandler:
    """图片处理器"""
    
    async def process(self, file_path: str) -> ProcessedFile:
        """处理图片文件"""
        path = Path(file_path)
        
        # 读取图片并转换为 base64
        with path.open("rb") as f:
            image_data = f.read()
        
        # 压缩图片（如果需要）
        base64_image = base64.b64encode(image_data).decode("utf-8")
        
        return ProcessedFile(
            type="image",
            content=f"[图片: {path.name}]",
            images=[base64_image],
            metadata={
                "size": len(image_data),
                "format": path.suffix[1:],
                "width": 0,  # 需要 PIL 获取
                "height": 0
            }
        )
