"""
LLM Engine 模块 - 负责与各大模型API交互
支持 DeepSeek (OpenAI兼容)、Ollama、Claude、OpenAI 等
提供统一的流式输出接口
"""

import hashlib
import json
import os
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator, Generator, Union
import logging
import httpx

# 加载环境变量（必须在其他导入之前）
from dotenv import load_dotenv
load_dotenv()  # 自动加载 .env 文件中的配置

try:
    import openai
    from openai import OpenAI, AsyncOpenAI
except ImportError:
    openai = None
    OpenAI = None
    AsyncOpenAI = None

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置文件路径
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
MODELS_CONFIG_PATH = CONFIG_DIR / "models_config.json"
AGENTS_CONFIG_PATH = CONFIG_DIR / "agents_config.json"
WORKSPACE_DIR = BASE_DIR / "workspace"

# 确保目录存在
WORKSPACE_DIR.mkdir(exist_ok=True)


class LLMEngine:
    """LLM引擎核心类，处理模型API调用"""

    def __init__(self):
        self.models_config = self._load_models_config()
        self.agents_config = self._load_agents_config()
        self.client_cache = {}  # 缓存不同模型的客户端
        self.config_hashes = {}  # 存储配置哈希，用于检测配置变更

    def clear_model_cache(self, model_id: str = None):
        """清除模型客户端缓存
        Args:
            model_id: 要清除的模型ID，如果为None则清除所有缓存
        """
        if model_id is None:
            self.client_cache.clear()
            self.config_hashes.clear()
            logger.info("Cleared all model client caches")
        elif model_id in self.client_cache:
            del self.client_cache[model_id]
            if model_id in self.config_hashes:
                del self.config_hashes[model_id]
            logger.info(f"Cleared cache for model: {model_id}")

    def reload_configs(self):
        """重新加载所有配置（当配置文件被修改后调用）"""
        old_models_config = self.models_config
        self.models_config = self._load_models_config()
        self.agents_config = self._load_agents_config()

        # 清除所有缓存，因为配置可能已更改
        self.client_cache.clear()
        self.config_hashes.clear()
        logger.info("Reloaded all configurations and cleared caches")

        # 检查配置是否实际更改
        if json.dumps(old_models_config, sort_keys=True) != json.dumps(self.models_config, sort_keys=True):
            logger.info("Models configuration has been updated")

    def _load_models_config(self) -> Dict[str, Any]:
        """加载模型配置，并尝试从环境变量覆盖敏感信息"""
        config = {"models": []}
        try:
            if MODELS_CONFIG_PATH.exists():
                with open(MODELS_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
        except Exception as e:
            logger.error(f"加载模型配置失败: {e}")
        
        # 尝试从环境变量覆盖配置
        models = config.get("models", [])
        for model in models:
            model_id = model.get("id")
            if not model_id:
                continue
            
            # 将模型ID转换为环境变量前缀 (例如: deepseek-chat -> DEEPSEEK_CHAT)
            prefix = model_id.upper().replace("-", "_").replace(".", "_")
            
            # 检查并覆盖 API Key
            env_api_key = os.environ.get(f"{prefix}_API_KEY")
            if env_api_key:
                model["api_key"] = env_api_key
                
            # 检查并覆盖 API Base
            env_api_base = os.environ.get(f"{prefix}_API_BASE")
            if env_api_base:
                model["api_base"] = env_api_base
                
            # 检查并覆盖 Default Model
            env_default_model = os.environ.get(f"{prefix}_DEFAULT_MODEL")
            if env_default_model:
                model["default_model"] = env_default_model

        return config

    def _load_agents_config(self) -> Dict[str, Any]:
        """加载Agent配置"""
        try:
            if AGENTS_CONFIG_PATH.exists():
                with open(AGENTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载Agent配置失败: {e}")
        return {"agents": []}

    def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """根据模型ID获取配置"""
        for model in self.models_config.get("models", []):
            if model.get("id") == model_id:
                return model
        return None

    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """根据Agent ID获取配置"""
        for agent in self.agents_config.get("agents", []):
            if agent.get("id") == agent_id:
                return agent
        return None

    def get_agent_model_id(self, agent_id: str) -> str:
        """获取Agent对应的模型ID"""
        # 先从模型映射中查找
        mapping = self.models_config.get("model_mappings", {})
        if agent_id in mapping:
            model_id = mapping[agent_id]
            # 检查模型是否启用
            model_config = self.get_model_config(model_id)
            if model_config and model_config.get("active", False):
                return model_id

        # 回退到Agent自身的模型偏好
        agent_config = self.get_agent_config(agent_id)
        if agent_config:
            model_pref = agent_config.get("model_preference", "auto")
            if model_pref != "auto":
                model_config = self.get_model_config(model_pref)
                if model_config and model_config.get("active", False):
                    return model_pref

        # 默认使用第一个启用的模型
        for model in self.models_config.get("models", []):
            if model.get("active", False) and model.get("id") != "auto":
                return model.get("id")

        return "deepseek"  # 最终回退

    def _get_client(self, model_id: str):
        """获取或创建OpenAI客户端"""
        if OpenAI is None:
            raise ImportError("OpenAI SDK未安装，请运行: pip install openai")

        if model_id in self.client_cache:
            return self.client_cache[model_id]

        model_config = self.get_model_config(model_id)
        if not model_config:
            raise ValueError(f"未找到模型配置: {model_id}")

        api_key = model_config.get("api_key", "")
        api_base = model_config.get("api_base", "")

        # 如果仍然为空且不是本地模型，则报错
        # 注意：_load_models_config 已经尝试从环境变量加载了 api_key
        if not api_key and model_config.get("type") != "local":
            raise ValueError(f"未设置模型 {model_id} 的API密钥")

        # 创建自定义HTTP客户端，避免代理干扰
        http_client = httpx.Client(
            timeout=model_config.get("timeout", 120)
        )

        # 创建OpenAI客户端
        client = OpenAI(
            api_key=api_key,
            base_url=api_base if api_base else None,
            http_client=http_client
        )

        # 调试信息
        logger.info(f"LLM Client created for model: {model_id}")
        logger.info(f"  API Base: {api_base}")
        logger.info(f"  API Key present: {'Yes' if api_key else 'No'}")
        logger.info(f"  Timeout: {model_config.get('timeout', 120)}s")

        self.client_cache[model_id] = client
        return client

    def generate_stream(
        self,
        agent_id: str,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        生成流式响应

        Args:
            agent_id: Agent ID
            message: 用户消息
            history: 对话历史，格式为 [{"role": "user/assistant", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大令牌数

        Yields:
            生成的文本片段
        """
        # 定义变量以便在except块中访问
        model_id = None
        model_config = None

        try:
            # 获取Agent配置和系统提示词
            agent_config = self.get_agent_config(agent_id)
            system_prompt = agent_config.get("system_prompt", "") if agent_config else ""

            # 获取模型ID
            model_id = self.get_agent_model_id(agent_id)
            model_config = self.get_model_config(model_id)

            if not model_config:
                yield "❌ 错误：未找到可用的模型配置"
                return

            # 检查模型是否启用
            if not model_config.get("active", False):
                yield f"❌ 错误：模型 '{model_config.get('name')}' 未启用"
                return

            # 构建消息列表
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # 添加历史记录
            if history:
                for msg in history[-10:]:  # 只保留最近10条历史记录
                    if msg.get("role") in ["user", "assistant"]:
                        messages.append({"role": msg["role"], "content": msg["content"]})

            # 添加当前消息
            messages.append({"role": "user", "content": message})

            # 获取客户端
            client = self._get_client(model_id)

            # 调试信息
            logger.info(f"Generating stream for agent: {agent_id}, model: {model_id}")
            logger.info(f"  Model name: {model_config.get('default_model', model_config.get('id'))}")
            logger.info(f"  Messages count: {len(messages)}")
            logger.info(f"  Temperature: {temperature}")

            # 获取模型名称
            model_name = model_config.get("default_model", model_config.get("id"))

            # 流式调用
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or model_config.get("max_tokens", 1600),
                stream=True
            )

            # 流式返回
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

        except Exception as e:
            # 打印详细错误信息到终端以便调试
            print(f"LLM Connection Error Details:")
            print(f"Agent ID: {agent_id}")
            print(f"Model ID: {model_id}")
            print(f"Model Config: {model_config}")
            print(f"Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")

            error_msg = f"❌ LLM调用失败: {str(e)}"
            logger.error(error_msg)
            yield error_msg

    def generate_task_document(
        self,
        user_request: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成任务文档并保存到workspace目录

        Args:
            user_request: 用户需求
            output_path: 输出文件路径，默认为 workspace/task.md

        Returns:
            生成的Markdown内容
        """
        try:
            # 获取助理Agent的配置
            assistant_config = self.get_agent_config("assistant")
            if not assistant_config:
                return "❌ 错误：未找到助理Agent配置"

            # 使用助理的系统提示词
            system_prompt = assistant_config.get("system_prompt", "")

            # 构建提示词
            task_prompt = f"""请将以下用户需求转化为标准任务文档：

用户需求：{user_request}

请按照以下格式输出：
# 任务标题
（简洁明了的任务标题）

## 任务描述
（详细的任务描述，包括背景、目标、范围等）

## 验收标准
（清晰可衡量的验收标准，用于判断任务是否完成）

## 注意事项
（需要注意的事项、约束条件、风险提示等）

## 技能要求
（完成任务所需的具体技能）

请直接输出Markdown格式，不要添加额外说明。"""

            # 调用模型生成任务文档
            model_id = self.get_agent_model_id("assistant")
            model_config = self.get_model_config(model_id)

            if not model_config or not model_config.get("active", False):
                return "❌ 错误：没有可用的模型来生成任务文档"

            client = self._get_client(model_id)
            model_name = model_config.get("default_model", model_config.get("id"))

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task_prompt}
                ],
                temperature=0.3,  # 使用较低温度确保稳定性
                max_tokens=2000
            )

            task_content = response.choices[0].message.content

            # 保存到文件
            if output_path is None:
                output_path = WORKSPACE_DIR / "task.md"
            else:
                output_path = Path(output_path)

            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(task_content)

            logger.info(f"任务文档已保存到: {output_path}")
            return task_content

        except Exception as e:
            error_msg = f"❌ 生成任务文档失败: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def test_connection(self, model_id: str) -> str:
        """
        测试模型连接

        Args:
            model_id: 模型ID

        Returns:
            测试结果信息
        """
        try:
            model_config = self.get_model_config(model_id)
            if not model_config:
                return f"❌ 错误：未找到模型配置 '{model_id}'"

            if not model_config.get("active", False):
                return f"⚠️ 警告：模型 '{model_config.get('name')}' 未启用"

            # 测试连接
            client = self._get_client(model_id)

            # 发送一个简单的测试请求
            model_name = model_config.get("default_model", model_config.get("id"))

            # 对于本地模型，可能不需要API密钥
            if model_config.get("type") == "local" and not model_config.get("api_key"):
                # 尝试简单的请求
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    return f"✅ 连接成功！模型: {model_name}"
                except Exception as e:
                    return f"❌ 连接测试失败: {str(e)}"
            else:
                # 对于云模型，需要API密钥
                api_key = model_config.get("api_key", "")
                if not api_key:
                    return f"❌ 错误：未设置API密钥，请检查 {model_id} 配置"

                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    return f"✅ 连接成功！模型: {model_name}"
                except Exception as e:
                    return f"❌ 连接测试失败: {str(e)}"

        except Exception as e:
            return f"❌ 连接测试失败: {str(e)}"


# 全局实例
_llm_engine_instance = None

def get_llm_engine() -> LLMEngine:
    """获取LLM引擎单例实例"""
    global _llm_engine_instance
    if _llm_engine_instance is None:
        _llm_engine_instance = LLMEngine()
    return _llm_engine_instance