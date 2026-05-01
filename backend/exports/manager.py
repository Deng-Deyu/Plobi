"""
文件导出管理器
Phase 3: 任务输出到 workspace/exports/

按 Agent 类型分类，文件命名包含时间戳和任务 ID。
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List
from dataclasses import dataclass, asdict
import uuid


@dataclass
class ExportedFile:
    """导出文件信息"""
    id: str
    agent_id: str
    task_id: str
    filename: str
    relative_path: str
    absolute_path: str
    size: int
    mime_type: str
    created_at: str
    description: str = ""


class ExportManager:
    """文件导出管理器"""

    def __init__(self, workspace_dir: Optional[Path] = None):
        if workspace_dir is None:
            # backend/exports/manager.py -> backend/ -> workspace/
            workspace_dir = Path(__file__).resolve().parent.parent / "workspace"
        self.workspace_dir = workspace_dir
        self.exports_dir = workspace_dir / "exports"
        self.index_file = self.exports_dir / "index.json"
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """确保目录结构存在"""
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建各 Agent 的输出目录
        agent_dirs = ["researcher", "engineer", "publisher", "musician", "videographer", "master"]
        for agent_id in agent_dirs:
            (self.exports_dir / agent_id).mkdir(exist_ok=True)

    def _load_index(self) -> dict:
        """加载文件索引"""
        if not self.index_file.exists():
            return {}
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self, index: dict) -> None:
        """保存文件索引"""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _generate_filename(self, agent_id: str, task_id: str, original_name: str) -> str:
        """生成文件名：时间戳_任务ID_原始文件名"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        # 清理任务 ID 中的特殊字符
        clean_task_id = task_id.replace("-", "_")[:16]
        # 提取原始文件扩展名
        ext = Path(original_name).suffix
        base_name = Path(original_name).stem
        return f"{timestamp}_{clean_task_id}_{base_name}{ext}"

    def export_file(
        self,
        agent_id: str,
        task_id: str,
        source_path: str,
        description: str = "",
        copy: bool = True
    ) -> ExportedFile:
        """导出文件到 workspace/exports/

        Args:
            agent_id: Agent ID（如 "researcher", "engineer"）
            task_id: 任务 ID
            source_path: 源文件路径
            description: 文件描述
            copy: 是否复制文件（False 则移动）

        Returns:
            ExportedFile: 导出文件信息
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在: {source_path}")

        # 确定目标目录
        target_dir = self.exports_dir / agent_id
        target_dir.mkdir(exist_ok=True)

        # 生成文件名
        filename = self._generate_filename(agent_id, task_id, source.name)
        target_path = target_dir / filename

        # 复制或移动文件
        if copy:
            shutil.copy2(source, target_path)
        else:
            shutil.move(str(source), str(target_path))

        # 计算相对路径
        relative_path = f"exports/{agent_id}/{filename}"

        # 创建导出记录
        file_id = str(uuid.uuid4())
        exported_file = ExportedFile(
            id=file_id,
            agent_id=agent_id,
            task_id=task_id,
            filename=filename,
            relative_path=relative_path,
            absolute_path=str(target_path.resolve()),
            size=target_path.stat().st_size,
            mime_type=self._guess_mime_type(filename),
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description
        )

        # 更新索引
        index = self._load_index()
        index[file_id] = asdict(exported_file)
        self._save_index(index)

        return exported_file

    def export_content(
        self,
        agent_id: str,
        task_id: str,
        content: str,
        filename: str,
        description: str = ""
    ) -> ExportedFile:
        """导出文本内容到文件

        Args:
            agent_id: Agent ID
            task_id: 任务 ID
            content: 文件内容
            filename: 文件名
            description: 文件描述

        Returns:
            ExportedFile: 导出文件信息
        """
        # 确定目标目录
        target_dir = self.exports_dir / agent_id
        target_dir.mkdir(exist_ok=True)

        # 生成文件名
        final_filename = self._generate_filename(agent_id, task_id, filename)
        target_path = target_dir / final_filename

        # 写入文件
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 计算相对路径
        relative_path = f"exports/{agent_id}/{final_filename}"

        # 创建导出记录
        file_id = str(uuid.uuid4())
        exported_file = ExportedFile(
            id=file_id,
            agent_id=agent_id,
            task_id=task_id,
            filename=final_filename,
            relative_path=relative_path,
            absolute_path=str(target_path.resolve()),
            size=target_path.stat().st_size,
            mime_type=self._guess_mime_type(final_filename),
            created_at=datetime.now(timezone.utc).isoformat(),
            description=description
        )

        # 更新索引
        index = self._load_index()
        index[file_id] = asdict(exported_file)
        self._save_index(index)

        return exported_file

    def list_files(self, agent_id: Optional[str] = None) -> List[ExportedFile]:
        """列出导出的文件

        Args:
            agent_id: 过滤特定 Agent 的文件，None 表示全部

        Returns:
            List[ExportedFile]: 文件列表
        """
        index = self._load_index()
        files = []
        for file_id, data in index.items():
            if agent_id is None or data.get("agent_id") == agent_id:
                files.append(ExportedFile(**data))
        # 按创建时间倒序排列
        files.sort(key=lambda x: x.created_at, reverse=True)
        return files

    def get_file(self, file_id: str) -> Optional[ExportedFile]:
        """获取单个文件信息"""
        index = self._load_index()
        data = index.get(file_id)
        if data:
            return ExportedFile(**data)
        return None

    def delete_file(self, file_id: str) -> bool:
        """删除导出的文件"""
        index = self._load_index()
        data = index.get(file_id)
        if not data:
            return False

        # 删除物理文件
        file_path = Path(data.get("absolute_path"))
        if file_path.exists():
            file_path.unlink()

        # 从索引中移除
        del index[file_id]
        self._save_index(index)
        return True

    def _guess_mime_type(self, filename: str) -> str:
        """根据文件扩展名猜测 MIME 类型"""
        ext = Path(filename).suffix.lower()
        mime_map = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".mp4": "video/mp4",
            ".gp": "application/octet-stream",
            ".gpx": "application/octet-stream",
            ".json": "application/json",
            ".xml": "application/xml",
            ".html": "text/html",
        }
        return mime_map.get(ext, "application/octet-stream")


# 全局单例
export_manager = ExportManager()
