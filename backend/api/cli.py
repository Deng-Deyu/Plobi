"""
CLI 工具管理 API 端点
Phase 3: CLI 工具封装

提供 CLI 工具的列表、执行、启用/禁用功能。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from sandbox.executor import cli_executor

router = APIRouter(prefix="/cli", tags=["cli"])


# ─── Pydantic Models ──────────────────────────────────────

class ExecuteCLIRequest(BaseModel):
    tool_name: str
    args: list[str] = []
    cwd: Optional[str] = None
    timeout: Optional[int] = None


# ─── Endpoints ────────────────────────────────────────────

@router.get("/tools")
async def list_tools():
    """列出所有 CLI 工具及其状态"""
    return cli_executor.list_tools()


@router.post("/execute")
async def execute_cli(body: ExecuteCLIRequest):
    """执行 CLI 命令"""
    result = await cli_executor.run(
        tool_name=body.tool_name,
        args=body.args,
        cwd=body.cwd,
        timeout=body.timeout
    )
    return {
        "success": result.success,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.return_code,
        "error": result.error
    }


@router.put("/{tool_name}/enable")
async def enable_tool(tool_name: str):
    """启用工具"""
    success = cli_executor.enable_tool(tool_name)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "ok", "tool": tool_name, "enabled": True}


@router.put("/{tool_name}/disable")
async def disable_tool(tool_name: str):
    """禁用工具"""
    success = cli_executor.disable_tool(tool_name)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "ok", "tool": tool_name, "enabled": False}
