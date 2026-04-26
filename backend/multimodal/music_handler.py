"""
乐谱处理器
Phase 2: 多模态输入
"""

from pathlib import Path

from multimodal.types import ProcessedFile


class MusicHandler:
    """乐谱处理器（Guitar Pro 格式）"""
    
    async def process_guitar_pro(self, file_path: str) -> ProcessedFile:
        """处理 Guitar Pro 文件"""
        path = Path(file_path)
        
        # Phase 2: 简化版，只返回基本信息
        # Phase 3: 集成 music21 解析乐谱结构
        
        return ProcessedFile(
            type="music",
            content=f"[Guitar Pro 乐谱: {path.name}]",
            images=[],
            metadata={
                "size": path.stat().st_size,
                "format": path.suffix[1:],
                "tracks": 0,  # 需要 music21 获取
                "bpm": 0,
                "key": "Unknown"
            }
        )
