"""
子 Agent 基类
Phase 2: Agent 抽象层
Phase 3: MCP 工具调用支持
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from .router import router
from memory.agent_memory import get_context_injection
from mcpclient.client import mcp_manager


class BaseAgent(ABC):
    """子 Agent 基类"""
    
    def __init__(self, agent_id: str, config: dict):
        self.agent_id = agent_id
        self.name = config.get("name", agent_id)
        self.config = config
        self.mcp_servers: list[str] = config.get("mcp_servers", [])
        self.system_prompt = self._build_system_prompt()
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        pass
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, args: dict) -> str:
        """调用 MCP Server 的工具
        
        优雅降级：如果 MCP Server 不可用，返回错误信息而非崩溃。
        """
        try:
            result = await mcp_manager.call_tool(server_name, tool_name, args)
            return result
        except Exception as e:
            return f"[MCP Error] {server_name}/{tool_name}: {e}"
    
    async def list_available_tools(self) -> dict[str, list[dict]]:
        """列出当前 Agent 可用的所有 MCP 工具"""
        all_tools: dict[str, list[dict]] = {}
        for server_name in self.mcp_servers:
            tools = await mcp_manager.list_tools(server_name)
            if tools:
                all_tools[server_name] = tools
        return all_tools
    
    async def execute(
        self,
        task_description: str,
        input_data: Optional[str] = None,
        memory_context: str = ""
    ) -> str:
        """执行任务"""
        # 构建消息
        system_content = self.system_prompt
        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        # 如果有 MCP 工具可用，注入工具描述到系统提示
        if self.mcp_servers:
            tools_desc = await self._build_tools_description()
            if tools_desc:
                system_content += f"\n\n你可以使用以下 MCP 工具：\n{tools_desc}"
        
        user_content = f"任务描述：{task_description}"
        if input_data:
            user_content += f"\n\n输入数据：{input_data}"
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_content)
        ]
        
        # 调用 LLM
        provider = self.config.get("model", {}).get("provider", "deepseek")
        model_id = self.config.get("model", {}).get("model_id")
        temperature = self.config.get("model", {}).get("temperature", 0.7)
        max_tokens = self.config.get("model", {}).get("max_tokens", 4096)
        
        response = await router.invoke(
            provider=provider,
            messages=messages,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response
    
    async def _build_tools_description(self) -> str:
        """构建 MCP 工具描述文本，注入到系统提示中"""
        lines: list[str] = []
        for server_name in self.mcp_servers:
            tools = await mcp_manager.list_tools(server_name)
            if tools:
                lines.append(f"### {server_name}")
                for tool in tools:
                    lines.append(f"- **{tool['name']}**: {tool['description']}")
        return "\n".join(lines) if lines else ""
    
    async def chat(
        self,
        user_message: str,
        memory_context: str = ""
    ) -> str:
        """直接对话（绕过 Master）"""
        system_content = self.system_prompt
        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_message)
        ]
        
        provider = self.config.get("model", {}).get("provider", "deepseek")
        model_id = self.config.get("model", {}).get("model_id")
        temperature = self.config.get("model", {}).get("temperature", 0.7)
        max_tokens = self.config.get("model", {}).get("max_tokens", 4096)
        
        response = await router.invoke(
            provider=provider,
            messages=messages,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response
