"""
出版官 Agent 实现
Phase 3: PPT/课程/科研论文/技术文档制作

生成 Markdown 格式文档并保存到 workspace/exports/documents/。
如果系统安装了 Marp CLI 或 Pandoc，自动转换为 PPT/PDF。
"""

import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from .base_agent import BaseAgent


class PublisherAgent(BaseAgent):
    """出版官：PPT/课程/科研论文/技术文档制作"""

    WORKSPACE = Path(__file__).resolve().parent.parent / "workspace" / "exports" / "documents"

    def _build_system_prompt(self) -> str:
        return f"""你是出版官，负责 PPT/课程/科研论文/技术文档制作。

你的职责：
1. 将研究资料整理成高质量的演示文稿或文档
2. 使用 Markdown 格式输出内容
3. 结构清晰、逻辑严谨
4. 符合学术和商业标准

输出格式：
## 文档结构
{{大纲}}

## 内容生成
{{具体内容}}

## 格式说明
{{格式要求}}

注意：
- 使用 Markdown 语法（标题、列表、表格、代码块等）
- 内容要专业、有条理
- 如果是演示文稿，每页用 `---` 分隔（Marp 格式）
"""

    async def execute(
        self,
        task_description: str,
        input_data: Optional[str] = None,
        memory_context: str = ""
    ) -> str:
        """执行任务：生成文档并保存为文件"""
        # 先生成内容
        result = await super().execute(
            task_description=task_description,
            input_data=input_data,
            memory_context=memory_context
        )

        # 保存为 Markdown 文件
        output_dir = self.WORKSPACE
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_id = str(uuid.uuid4())[:8]
        filename = f"document_{plan_id}_{timestamp}.md"
        filepath = output_dir / filename

        try:
            filepath.write_text(result, encoding="utf-8")
            file_info = f"\n\n[文件已保存] {filepath}"
        except Exception as e:
            file_info = f"\n\n[文件保存失败] {e}"

        return result + file_info
