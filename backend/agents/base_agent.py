"""
子 Agent 基类
Phase 2: Agent 抽象层
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from .router import router
from memory.agent_memory import get_context_injection


class BaseAgent(ABC):
    """子 Agent 基类"""
    
    def __init__(self, agent_id: str, config: dict):
        self.agent_id = agent_id
        self.name = config.get("name", agent_id)
        self.config = config
        self.system_prompt = self._build_system_prompt()
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        pass
    
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
