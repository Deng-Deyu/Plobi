"""
代码执行沙盒
Phase 4: 工程师 Agent 代码执行能力

提供安全的 Python 代码执行环境，执行前需前端确认。
"""

import asyncio
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/sandbox", tags=["sandbox"])

# 待确认的执行请求
_pending_executions: dict[str, dict] = {}


class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"  # python | shell
    description: str = ""  # 工程师对这段代码的说明
    agent_id: str = "engineer"
    session_id: str = ""


class CodeConfirmRequest(BaseModel):
    execution_id: str
    approved: bool


@router.post("/propose")
async def propose_execution(body: CodeExecutionRequest):
    """工程师提交代码执行请求，等待用户确认"""
    execution_id = f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
    
    _pending_executions[execution_id] = {
        "execution_id": execution_id,
        "code": body.code,
        "language": body.language,
        "description": body.description,
        "agent_id": body.agent_id,
        "session_id": body.session_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    
    return {
        "execution_id": execution_id,
        "status": "pending",
        "code": body.code,
        "language": body.language,
        "description": body.description,
    }


@router.get("/pending")
async def list_pending():
    """列出待确认的执行请求"""
    return [
        exec_data for exec_data in _pending_executions.values()
        if exec_data["status"] == "pending"
    ]


@router.post("/confirm")
async def confirm_execution(body: CodeConfirmRequest):
    """用户确认或拒绝执行"""
    exec_data = _pending_executions.get(body.execution_id)
    if not exec_data:
        raise HTTPException(status_code=404, detail="Execution request not found")
    
    if exec_data["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Execution already {exec_data['status']}")
    
    if not body.approved:
        exec_data["status"] = "rejected"
        return {"execution_id": body.execution_id, "status": "rejected"}
    
    # Execute the code
    exec_data["status"] = "running"
    
    try:
        if exec_data["language"] == "python":
            result = await _execute_python(exec_data["code"])
        elif exec_data["language"] == "shell":
            result = await _execute_shell(exec_data["code"])
        else:
            result = {"stdout": "", "stderr": f"Unsupported language: {exec_data['language']}", "exit_code": 1}
        
        exec_data["status"] = "completed"
        exec_data["result"] = result
        return {"execution_id": body.execution_id, "status": "completed", "result": result}
    
    except Exception as e:
        exec_data["status"] = "error"
        exec_data["result"] = {"stdout": "", "stderr": str(e), "exit_code": 1}
        return {"execution_id": body.execution_id, "status": "error", "result": exec_data["result"]}


@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    """获取执行结果"""
    exec_data = _pending_executions.get(execution_id)
    if not exec_data:
        raise HTTPException(status_code=404, detail="Execution not found")
    return exec_data


async def _execute_python(code: str, timeout: int = 30) -> dict:
    """在子进程中执行 Python 代码"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name
    
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, temp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(Path(__file__).resolve().parent.parent / "workspace"),
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return {"stdout": "", "stderr": f"Execution timed out after {timeout}s", "exit_code": -1}
        
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode,
        }
    finally:
        os.unlink(temp_path)


async def _execute_shell(command: str, timeout: int = 30) -> dict:
    """执行 Shell 命令"""
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(Path(__file__).resolve().parent.parent / "workspace"),
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return {"stdout": "", "stderr": f"Execution timed out after {timeout}s", "exit_code": -1}
    
    return {
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "exit_code": proc.returncode,
    }
