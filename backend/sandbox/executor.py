"""
CLI 工具执行器
Phase 3: CLI 工具封装

支持跨平台命令白名单、审计日志、优雅降级。
"""

import asyncio
import sys
import platform
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CLIResult:
    """CLI 执行结果"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    error: str = ""


class CLIExecutor:
    """CLI 命令执行器，比 Python 沙盒权限更宽松，但仍有审计日志"""

    def __init__(self, whitelist_path: Optional[Path] = None):
        if whitelist_path is None:
            whitelist_path = Path(__file__).resolve().parent.parent / "config" / "cli_whitelist.json"
        self.whitelist_path = whitelist_path
        self.whitelist = self._load_whitelist()
        self.audit_log_path = Path(self.whitelist.get("audit_log", "backend/config/cli_audit.log"))
        self.platform = platform.system().lower()

    def _load_whitelist(self) -> dict:
        """加载白名单配置"""
        if not self.whitelist_path.exists():
            logger.warning(f"Whitelist file not found: {self.whitelist_path}, using empty config")
            return {"tools": {}, "audit_log": "backend/config/cli_audit.log"}
        try:
            with open(self.whitelist_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load whitelist: {e}")
            return {"tools": {}, "audit_log": "backend/config/cli_audit.log"}

    def _save_whitelist(self) -> None:
        """保存白名单配置"""
        self.whitelist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.whitelist_path, "w", encoding="utf-8") as f:
            json.dump(self.whitelist, f, indent=2, ensure_ascii=False)

    def _get_tool_config(self, tool_name: str) -> Optional[dict]:
        """获取工具配置"""
        tools = self.whitelist.get("tools", {})
        config = tools.get(tool_name)
        if not config:
            return None
        return config

    def _resolve_command(self, tool_name: str) -> Optional[str]:
        """解析命令路径（支持跨平台 + sys_executable 占位符）"""
        config = self._get_tool_config(tool_name)
        if not config:
            return None

        paths = config.get("paths", {})
        command = paths.get(self.platform)

        if not command:
            return None

        # 替换 {sys_executable} 占位符
        if "{sys_executable}" in command:
            command = command.replace("{sys_executable}", sys.executable)

        return command

    async def _log_execution(self, tool_name: str, command: str, args: list[str], result: CLIResult) -> None:
        """记录审计日志"""
        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": tool_name,
                "command": command,
                "args": args,
                "success": result.success,
                "return_code": result.return_code,
                "error": result.error,
            }
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    async def run(
        self,
        tool_name: str,
        args: list[str],
        cwd: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> CLIResult:
        """执行 CLI 命令

        Args:
            tool_name: 工具名称（如 "python", "ffmpeg"）
            args: 命令参数
            cwd: 工作目录
            timeout: 超时时间（秒），默认使用配置中的值

        Returns:
            CLIResult: 执行结果
        """
        config = self._get_tool_config(tool_name)

        # 1. 检查工具是否在白名单中
        if not config:
            return CLIResult(
                success=False,
                error=f"工具 '{tool_name}' 不在白名单中"
            )

        # 2. 检查工具是否启用
        if not config.get("enabled", False):
            return CLIResult(
                success=False,
                error=f"工具 '{tool_name}' 未启用"
            )

        # 3. 检查工具是否已安装
        if not config.get("installed", False):
            return CLIResult(
                success=False,
                error=f"工具 '{tool_name}' 未配置或未安装"
            )

        # 4. 解析命令路径
        command = self._resolve_command(tool_name)
        if not command:
            return CLIResult(
                success=False,
                error=f"工具 '{tool_name}' 在当前平台 ({self.platform}) 未配置路径"
            )

        # 5. 合并参数
        base_args = config.get("args", [])
        full_args = base_args + args

        # 6. 确定超时时间
        exec_timeout = timeout or config.get("timeout", 120)

        # 7. 确定工作目录
        work_dir = cwd or str(Path(__file__).resolve().parent.parent.parent / "workspace")

        # 8. 执行命令
        try:
            proc = await asyncio.create_subprocess_exec(
                command,
                *full_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=exec_timeout)

            result = CLIResult(
                success=proc.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                return_code=proc.returncode
            )

            # 记录审计日志
            await self._log_execution(tool_name, command, full_args, result)

            return result

        except asyncio.TimeoutError:
            proc.kill()
            result = CLIResult(
                success=False,
                error=f"命令执行超时 ({exec_timeout}秒)"
            )
            await self._log_execution(tool_name, command, full_args, result)
            return result

        except Exception as e:
            result = CLIResult(
                success=False,
                error=f"命令执行失败: {e}"
            )
            await self._log_execution(tool_name, command, full_args, result)
            return result

    def list_tools(self) -> dict[str, dict]:
        """列出所有工具及其状态"""
        tools = self.whitelist.get("tools", {})
        result = {}
        for name, config in tools.items():
            result[name] = {
                "name": config.get("name", name),
                "description": config.get("description", ""),
                "enabled": config.get("enabled", False),
                "installed": config.get("installed", False),
                "platform": self.platform,
                "command": self._resolve_command(name) or "未配置"
            }
        return result

    def enable_tool(self, tool_name: str) -> bool:
        """启用工具"""
        config = self._get_tool_config(tool_name)
        if not config:
            return False
        config["enabled"] = True
        self._save_whitelist()
        return True

    def disable_tool(self, tool_name: str) -> bool:
        """禁用工具"""
        config = self._get_tool_config(tool_name)
        if not config:
            return False
        config["enabled"] = False
        self._save_whitelist()
        return True


# 全局单例
cli_executor = CLIExecutor()
