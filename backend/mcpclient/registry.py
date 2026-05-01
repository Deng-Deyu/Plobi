"""
MCP 插件注册表管理器
Phase 3: 插件与扩展

负责读写 plugins/registry.json，提供 CRUD 操作。
如果 registry.json 不存在或为空，自动初始化为空字典。
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone


REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent / "plugins" / "registry.json"


def _ensure_registry_file() -> None:
    """确保 registry.json 文件存在，不存在则创建空字典"""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text("{}", encoding="utf-8")


def load_registry() -> dict:
    """加载插件注册表，文件缺失时自动初始化"""
    _ensure_registry_file()
    try:
        content = REGISTRY_PATH.read_text(encoding="utf-8").strip()
        if not content:
            return {}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        # 文件损坏时返回空字典，不崩溃
        return {}


def save_registry(registry: dict) -> None:
    """保存插件注册表"""
    _ensure_registry_file()
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def list_plugins() -> list[dict]:
    """列出所有已注册插件"""
    registry = load_registry()
    return [v | {"id": k} for k, v in registry.items()]


def get_plugin(plugin_id: str) -> Optional[dict]:
    """获取单个插件信息"""
    registry = load_registry()
    entry = registry.get(plugin_id)
    if entry:
        return entry | {"id": plugin_id}
    return None


def add_plugin(plugin_id: str, entry: dict) -> dict:
    """添加插件到注册表"""
    registry = load_registry()
    entry["installed_at"] = datetime.now(timezone.utc).isoformat()
    entry["enabled"] = True
    registry[plugin_id] = entry
    save_registry(registry)
    return entry | {"id": plugin_id}


def remove_plugin(plugin_id: str) -> bool:
    """从注册表移除插件"""
    registry = load_registry()
    if plugin_id in registry:
        del registry[plugin_id]
        save_registry(registry)
        return True
    return False


def toggle_plugin(plugin_id: str) -> Optional[dict]:
    """切换插件启用/禁用状态"""
    registry = load_registry()
    if plugin_id not in registry:
        return None
    registry[plugin_id]["enabled"] = not registry[plugin_id].get("enabled", True)
    save_registry(registry)
    return registry[plugin_id] | {"id": plugin_id}


def get_enabled_mcp_servers() -> dict[str, dict]:
    """获取所有已启用的 MCP Server 配置"""
    registry = load_registry()
    return {
        k: v for k, v in registry.items()
        if v.get("enabled", True) and v.get("type", "").startswith("mcp")
    }
