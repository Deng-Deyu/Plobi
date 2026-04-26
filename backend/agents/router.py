"""
多模型路由器
Phase 2: LLM 抽象层
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()


class ModelRouter:
    """多模型路由器，支持不同 Agent 使用不同模型"""
    
    def __init__(self):
        self._clients: Dict[str, ChatOpenAI] = {}
        self._configs: Dict[str, Dict[str, Any]] = {
            "deepseek": {
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "model": "deepseek-chat",
            },
            "deepseek-coder": {
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "model": "deepseek-coder",
            },
            "anthropic": {
                "api_key": os.getenv("CLAUDE_API_KEY", ""),
                "model": "claude-opus-4-5",
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "model": "gpt-4o",
            },
        }
    
    def get_client(self, provider: str, model_id: Optional[str] = None, **kwargs) -> ChatOpenAI:
        """获取 LLM 客户端"""
        cache_key = f"{provider}:{model_id or 'default'}"
        
        if cache_key not in self._clients:
            config = self._configs.get(provider, {})
            
            if provider == "deepseek" or provider == "deepseek-coder":
                client = ChatOpenAI(
                    base_url=config.get("base_url"),
                    api_key=config.get("api_key"),
                    model=model_id or config.get("model"),
                    **kwargs
                )
            elif provider == "anthropic":
                client = ChatOpenAI(
                    api_key=config.get("api_key"),
                    model=model_id or config.get("model"),
                    **kwargs
                )
            elif provider == "openai":
                client = ChatOpenAI(
                    api_key=config.get("api_key"),
                    model=model_id or config.get("model"),
                    **kwargs
                )
            else:
                # 默认使用 DeepSeek
                client = ChatOpenAI(
                    base_url=self._configs["deepseek"]["base_url"],
                    api_key=self._configs["deepseek"]["api_key"],
                    model="deepseek-chat",
                    **kwargs
                )
            
            self._clients[cache_key] = client
        
        return self._clients[cache_key]
    
    async def invoke(
        self,
        provider: str,
        messages: list,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False
    ) -> str:
        """调用 LLM"""
        client = self.get_client(provider, model_id, temperature=temperature, max_tokens=max_tokens)
        
        if stream:
            # 流式调用
            response = ""
            async for chunk in client.astream(messages):
                if chunk.content:
                    response += chunk.content
            return response
        else:
            # 非流式调用
            result = await client.ainvoke(messages)
            return result.content


# 全局单例
router = ModelRouter()
