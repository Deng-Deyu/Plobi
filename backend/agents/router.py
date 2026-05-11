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
        _deepseek_base = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("DEEPSEEK_API_BASE") or "https://api.deepseek.com"
        # Ensure base_url ends with /v1 for LangChain ChatOpenAI compatibility
        if not _deepseek_base.rstrip("/").endswith("/v1"):
            _deepseek_base = _deepseek_base.rstrip("/") + "/v1"
        self._configs: Dict[str, Dict[str, Any]] = {
            "deepseek": {
                "base_url": _deepseek_base,
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "model": "deepseek-chat",
            },
            "deepseek-coder": {
                "base_url": _deepseek_base,
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
                import httpx
                # 明确对 DeepSeek 禁用代理，防止本地代理 (如 Clash/v2ray) 导致 httpx 异步连接 TLS 握手失败
                http_async_client = httpx.AsyncClient(proxy=None)
                http_client = httpx.Client(proxy=None)
                
                client = ChatOpenAI(
                    base_url=config.get("base_url"),
                    api_key=config.get("api_key"),
                    model=model_id or config.get("model"),
                    http_client=http_client,
                    http_async_client=http_async_client,
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
    ) -> str:
        """调用 LLM"""
        client = self.get_client(provider, model_id, temperature=temperature, max_tokens=max_tokens)
        result = await client.ainvoke(messages)
        return result.content

    async def astream(
        self,
        provider: str,
        messages: list,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """流式调用 LLM，返回异步生成器"""
        client = self.get_client(provider, model_id, temperature=temperature, max_tokens=max_tokens)
        async for chunk in client.astream(messages):
            if chunk.content:
                yield chunk.content


# 全局单例
router = ModelRouter()
