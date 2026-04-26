"""
音频处理器
Phase 2: 多模态输入
"""

from pathlib import Path

from multimodal.types import ProcessedFile


class AudioHandler:
    """音频处理器"""
    
    async def process(self, file_path: str) -> ProcessedFile:
        """处理音频文件"""
        path = Path(file_path)
        
        # Phase 2: 简化版，只返回基本信息
        # Phase 3: 集成 Librosa 进行音频分析
        
        return ProcessedFile(
            type="audio",
            content=f"[音频: {path.name}]",
            images=[],
            metadata={
                "size": path.stat().st_size,
                "format": path.suffix[1:],
                "duration": 0,  # 需要 Librosa 获取
                "bpm": 0,
                "key": "Unknown"
            }
        )
