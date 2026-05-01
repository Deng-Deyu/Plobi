"""
MCP Client Manager
Phase 3: 插件与扩展

统一管理所有 MCP Server 连接，按需启动 stdio 进程，复用连接。
使用官方 mcp Python SDK (Anthropic)。
"""

import asyncio
import logging
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcpclient.registry import get_enabled_mcp_servers

logger = logging.getLogger(__name__)


class MCPClientManager:
    """统一管理所有 MCP Server 连接，按需启动，复用连接"""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._contexts: dict[str, object] = {}  # stdio_client 上下文管理器
        self._read_streams: dict[str, object] = {}
        self._write_streams: dict[str, object] = {}
        self._lock = asyncio.Lock()

    async def get_session(self, server_name: str) -> Optional[ClientSession]:
        """获取或创建 MCP Server 连接"""
        if server_name in self._sessions:
            return self._sessions[server_name]

        async with self._lock:
            # 双重检查
            if server_name in self._sessions:
                return self._sessions[server_name]

            servers = get_enabled_mcp_servers()
            config = servers.get(server_name)
            if not config:
                logger.warning(f"MCP Server '{server_name}' not found in registry")
                return None

            try:
                params = StdioServerParameters(
                    command=config["command"],
                    args=config.get("args", []),
                    env=config.get("env")
                )

                # 启动 stdio 客户端
                read_stream, write_stream = await stdio_client(params).__aenter__()
                session = ClientSession(read_stream, write_stream)
                await session.initialize()

                self._sessions[server_name] = session
                self._read_streams[server_name] = read_stream
                self._write_streams[server_name] = write_stream

                logger.info(f"MCP Server '{server_name}' connected successfully")
                return session

            except Exception as e:
                logger.error(f"Failed to connect MCP Server '{server_name}': {e}")
                return None

    async def list_tools(self, server_name: str) -> list[dict]:
        """列出 MCP Server 提供的所有工具"""
        session = await self.get_session(server_name)
        if not session:
            return []

        try:
            result = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                }
                for tool in result.tools
            ]
        except Exception as e:
            logger.error(f"Failed to list tools from '{server_name}': {e}")
            return []

    async def call_tool(self, server_name: str, tool_name: str, args: dict) -> str:
        """调用 MCP Server 的工具"""
        session = await self.get_session(server_name)
        if not session:
            return f"Error: MCP Server '{server_name}' not available"

        try:
            result = await session.call_tool(tool_name, args)
            # 提取文本内容
            if result.content:
                return "\n".join(
                    item.text for item in result.content
                    if hasattr(item, "text")
                )
            return str(result)
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}' on '{server_name}': {e}")
            return f"Error: {e}"

    async def list_all_tools(self) -> dict[str, list[dict]]:
        """列出所有已启用 MCP Server 的工具"""
        servers = get_enabled_mcp_servers()
        all_tools: dict[str, list[dict]] = {}
        for server_name in servers:
            tools = await self.list_tools(server_name)
            if tools:
                all_tools[server_name] = tools
        return all_tools

    async def close_session(self, server_name: str) -> None:
        """关闭指定 MCP Server 连接"""
        if server_name in self._sessions:
            try:
                session = self._sessions.pop(server_name)
                # 清理资源
                self._read_streams.pop(server_name, None)
                self._write_streams.pop(server_name, None)
                self._contexts.pop(server_name, None)
                logger.info(f"MCP Server '{server_name}' disconnected")
            except Exception as e:
                logger.error(f"Error closing MCP Server '{server_name}': {e}")

    async def close_all(self) -> None:
        """关闭所有 MCP Server 连接"""
        server_names = list(self._sessions.keys())
        for name in server_names:
            await self.close_session(name)


# 全局单例
mcp_manager = MCPClientManager()
