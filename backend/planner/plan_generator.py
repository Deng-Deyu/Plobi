"""
plan.md 生成器
Phase 2: 任务编排协议
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class PlanGenerator:
    """plan.md 任务书生成器"""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.plans_dir = workspace_dir / "plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(
        self,
        user_request: str,
        master_understanding: str,
        tasks: list[Dict[str, Any]],
        plan_id: Optional[str] = None
    ) -> str:
        """生成 plan.md 内容"""
        if not plan_id:
            plan_id = str(uuid.uuid4())
        
        now = datetime.now().isoformat()
        
        # 构建 plan.md 内容
        lines = [
            f"# Plan: {self._extract_title(user_request)}",
            "",
            f"**Plan ID**: {plan_id}",
            f"**创建时间**: {now}",
            "**状态**: dispatching",
            "",
            "## 用户原始需求",
            user_request,
            "",
            "## Master 理解",
            master_understanding,
            "",
            "## 任务分解",
            ""
        ]
        
        # 添加任务
        for i, task in enumerate(tasks, 1):
            lines.extend([
                f"### 任务 {i} — {task['agent_name']}",
                f"**负责 Agent**: {task['agent_id']}",
                f"**任务描述**: {task['description']}",
                f"**输入**: {task.get('input', '无')}",
                f"**预期产出**: {task.get('output', '无')}",
                f"**依赖**: {', '.join(task.get('dependencies', [])) or '无'}",
                "**状态**: pending",
                ""
            ])
        
        # 添加时间预估
        lines.extend([
            "## 时间预估",
            *[f"- 任务 {i}: ~{task.get('estimated_time', '未知')}" for i, task in enumerate(tasks, 1)],
            f"- 总计: ~{self._estimate_total(tasks)}"
        ])
        
        plan_content = "\n".join(lines)
        
        # 保存到文件
        plan_path = self.plans_dir / f"{plan_id}_plan.md"
        plan_path.write_text(plan_content, encoding="utf-8")
        
        return plan_content
    
    def _extract_title(self, user_request: str) -> str:
        """从用户需求中提取简短标题"""
        # 简化版：取前 20 个字符
        return user_request[:20] + "..." if len(user_request) > 20 else user_request
    
    def _estimate_total(self, tasks: list[Dict[str, Any]]) -> str:
        """估算总时间"""
        # 简化版：累加所有任务时间
        total_minutes = 0
        for task in tasks:
            time_str = task.get("estimated_time", "0分钟")
            if "分钟" in time_str:
                total_minutes += int(time_str.replace("分钟", ""))
        return f"{total_minutes}分钟"
    
    def update_status(self, plan_id: str, status: str) -> bool:
        """更新 plan.md 状态"""
        plan_path = self.plans_dir / f"{plan_id}_plan.md"
        if not plan_path.exists():
            return False
        
        content = plan_path.read_text(encoding="utf-8")
        # 替换状态行
        import re
        content = re.sub(
            r'\*\*状态\*\*: \w+',
            f'**状态**: {status}',
            content
        )
        plan_path.write_text(content, encoding="utf-8")
        return True
    
    def get_plan(self, plan_id: str) -> Optional[str]:
        """获取 plan.md 内容"""
        plan_path = self.plans_dir / f"{plan_id}_plan.md"
        if plan_path.exists():
            return plan_path.read_text(encoding="utf-8")
        return None
    
    def list_plans(self) -> list[Dict[str, Any]]:
        """列出所有 plan.md"""
        plans = []
        for plan_file in self.plans_dir.glob("*_plan.md"):
            plan_id = plan_file.stem.replace("_plan", "")
            content = plan_file.read_text(encoding="utf-8")
            plans.append({
                "plan_id": plan_id,
                "content": content,
                "path": str(plan_file)
            })
        return plans
