"""
多模态处理类型定义
Phase 2: 多模态输入
"""

from dataclasses import dataclass


@dataclass
class ProcessedFile:
    type: str  # text / image / audio / structured
    content: str  # 文字内容或 JSON 结构
    images: list[str]  # base64 图片列表
    metadata: dict  # 额外元信息
