"""
插件管理 API 端点
Phase 3: 插件与扩展

提供插件的安装、卸载、启用/禁用、列表查询功能。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from mcpclient.registry import (
    list_plugins,
    get_plugin,
    add_plugin,
    remove_plugin,
    toggle_plugin,
)
from mcpclient.client import mcp_manager

router = APIRouter(prefix="/plugins", tags=["plugins"])


# ─── Pydantic Models ──────────────────────────────────────

class InstallNpmPluginRequest(BaseModel):
    package_name: str
    description: str = ""
    args: list[str] = []
    env: Optional[dict] = None


class InstallLocalPluginRequest(BaseModel):
    plugin_id: str
    name: str
    description: str = ""
    plugin_type: str = "python"  # "python" | "mcp_npm" | "mcp_local"
    command: str = ""
    args: list[str] = []
    entry: str = ""
    provides: dict = {}
    requires: dict = {}


# ─── Endpoints ────────────────────────────────────────────

@router.get("")
async def list_plugins_api():
    """获取已安装插件列表"""
    plugins = list_plugins()
    return plugins


@router.get("/{plugin_id}")
async def get_plugin_api(plugin_id: str):
    """获取单个插件详情"""
    plugin = get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.post("/install/npm")
async def install_npm_plugin(body: InstallNpmPluginRequest):
    """安装 NPM 发布的 MCP Server

    使用 npx 方式运行，无需全局安装。
    """
    # 检查是否已安装
    existing = get_plugin(body.package_name)
    if existing:
        raise HTTPException(status_code=409, detail="Plugin already installed")

    entry = {
        "name": body.package_name,
        "type": "mcp_npm",
        "command": "npx",
        "args": ["-y", body.package_name] + body.args,
        "description": body.description,
        "env": body.env or {},
    }

    result = add_plugin(body.package_name, entry)
    return result


@router.post("/install/local")
async def install_local_plugin(body: InstallLocalPluginRequest):
    """安装本地插件"""
    existing = get_plugin(body.plugin_id)
    if existing:
        raise HTTPException(status_code=409, detail="Plugin already installed")

    entry = {
        "name": body.name,
        "type": body.plugin_type,
        "command": body.command,
        "args": body.args,
        "description": body.description,
        "entry": body.entry,
        "provides": body.provides,
        "requires": body.requires,
    }

    result = add_plugin(body.plugin_id, entry)
    return result


@router.delete("/{plugin_id}")
async def uninstall_plugin(plugin_id: str):
    """卸载插件"""
    # 先关闭 MCP 连接
    await mcp_manager.close_session(plugin_id)

    removed = remove_plugin(plugin_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "ok", "removed": plugin_id}


@router.put("/{plugin_id}/toggle")
async def toggle_plugin_api(plugin_id: str):
    """启用/禁用插件"""
    result = toggle_plugin(plugin_id)
    if not result:
        raise HTTPException(status_code=404, detail="Plugin not found")

    # 如果禁用，关闭连接
    if not result.get("enabled", True):
        await mcp_manager.close_session(plugin_id)

    return result


@router.get("/tools/all")
async def list_all_tools():
    """列出所有已启用 MCP Server 的工具"""
    try:
        tools = await mcp_manager.list_all_tools()
        return tools
    except Exception as e:
        return {"error": str(e), "message": "Failed to list tools. MCP Server may require additional configuration."}
