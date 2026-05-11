"""
Master Agent 实现
Phase 2: 中枢主控 + LLM 调用
"""

from typing import Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .router import router
from memory.agent_memory import get_context_injection


class MasterAgent:
    """Master Agent：中枢主控，负责对话、规划、调度"""
    
    def __init__(self):
        self.system_prompt = """你是 Plobi Agent 的 Master Agent（中枢主控）。

你的核心职责：
1. **意图澄清与追问**：如果用户的需求含糊不清或缺少关键信息（如目标受众、预期格式、特定约束、截止要求等），你必须**优先追问细节**，绝对不能在信息不足的情况下凭空瞎编或强行分配任务。
2. **任务评估与规划**：当需求明确且较为复杂（如需要研究、生成图表、开发代码、制作PPT、视频等）时，你将在回复的最后一行加上 `<NEED_PLAN>` 标签，系统将自动生成详细的任务书。
3. **直接回复**：对于简单的日常问答、概念解释，无需麻烦子Agent，直接回答即可，不要加标签。

对话规范：
- 用第一人称，态度专业、热情。
- 不要向用户展示内部的系统机制，直接沟通需求即可。
- 如果决定生成规划，回复中应告知用户：“好的，我已经了解了您的需求，我马上为您制定执行计划并分配任务。”，然后在末尾另起一行输出 `<NEED_PLAN>`。
"""
    
    async def chat(
        self,
        user_message: str,
        session_id: str,
        agent_config: dict,
        memory_context: str = ""
    ) -> dict:
        """与用户对话"""
        system_content = self.system_prompt
        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_message)
        ]
        
        provider = agent_config.get("model", {}).get("provider", "deepseek")
        model_id = agent_config.get("model", {}).get("model_id")
        temperature = agent_config.get("model", {}).get("temperature", 0.7)
        max_tokens = agent_config.get("model", {}).get("max_tokens", 4096)
        
        response = await router.invoke(
            provider=provider,
            messages=messages,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        needs_plan = "<NEED_PLAN>" in response
        # 移除标签
        response = response.replace("<NEED_PLAN>", "").strip()
        
        return {
            "content": response,
            "needs_plan": needs_plan,
            "agent_id": "master"
        }

    async def astream_chat(
        self,
        user_message: str,
        session_id: str,
        agent_config: dict,
        memory_context: str = ""
    ):
        """流式与用户对话"""
        system_content = self.system_prompt
        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_message)
        ]
        
        provider = agent_config.get("model", {}).get("provider", "deepseek")
        model_id = agent_config.get("model", {}).get("model_id")
        temperature = agent_config.get("model", {}).get("temperature", 0.7)
        max_tokens = agent_config.get("model", {}).get("max_tokens", 4096)
        
        full_response = ""
        buffer = ""
        async for chunk in router.astream(
            provider=provider,
            messages=messages,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            full_response += chunk
            buffer += chunk
            
            # 延迟发送以隐藏可能的 <NEED_PLAN> 标签
            if "<NEED_PLAN" in buffer:
                # 仍在累积标签，暂时不 yield
                if buffer.endswith(">"):
                    buffer = buffer.replace("<NEED_PLAN>", "")
                pass
            else:
                # 如果明确没有 <NEED_PLAN 前缀，清空buffer yield
                if "<" in buffer:
                    # 可能正在生成 <NEED_PLAN
                    idx = buffer.rfind("<")
                    if "<NEED_PLAN".startswith(buffer[idx:]):
                        safe_part = buffer[:idx]
                        if safe_part:
                            yield {"type": "token", "content": safe_part}
                        buffer = buffer[idx:]
                    else:
                        yield {"type": "token", "content": buffer}
                        buffer = ""
                else:
                    yield {"type": "token", "content": buffer}
                    buffer = ""
        
        # 兜底清理
        if buffer:
            buffer = buffer.replace("<NEED_PLAN>", "")
            if buffer:
                yield {"type": "token", "content": buffer}
            
        needs_plan = "<NEED_PLAN>" in full_response
        full_response_cleaned = full_response.replace("<NEED_PLAN>", "").strip()
        
        yield {"type": "done", "needs_plan": needs_plan, "content": full_response_cleaned}
    
    async def generate_plan(
        self,
        user_message: str,
        session_id: str,
        agent_config: dict
    ) -> dict:
        """生成 plan.md 任务书"""
        plan_prompt = f"""请根据以下用户需求，生成一个标准化的 plan.md 任务书。

用户需求：
{user_message}

plan.md 格式要求：
```markdown
# Plan: {{简短任务名}}

**Plan ID**: {{uuid}}
**创建时间**: {{ISO 8601}}
**状态**: dispatching

## 用户原始需求
{{用户原始输入，逐字引用}}

## Master 理解
{{Master 对需求的解读，澄清了哪些信息}}

## 任务分解

### 任务 1 — {{子 Agent 名称}}
**负责 Agent**: {{agent_id}}
**任务描述**: {{具体任务描述}}
**输入**: {{输入信息}}
**预期产出**: {{产出文件路径}}
**依赖**: 无
**状态**: pending

### 任务 2 — {{子 Agent 名称}}
**负责 Agent**: {{agent_id}}
**任务描述**: {{具体任务描述}}
**输入**: {{任务1的产出}}
**预期产出**: {{产出文件路径}}
**依赖**: 任务 1
**状态**: waiting

## 时间预估
- 任务 1: ~{{时间}}
- 任务 2: ~{{时间}}
- 总计: ~{{总时间}}
```

请只输出 plan.md 内容，不要包含其他解释。"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=plan_prompt)
        ]
        
        provider = agent_config.get("model", {}).get("provider", "deepseek")
        model_id = agent_config.get("model", {}).get("model_id")
        
        plan_content = await router.invoke(
            provider=provider,
            messages=messages,
            model_id=model_id,
            temperature=0.5,
            max_tokens=4096
        )
        
        return {
            "plan_content": plan_content,
            "plan_id": self._extract_plan_id(plan_content)
        }
    
    def _extract_plan_id(self, plan_content: str) -> str:
        """从 plan.md 中提取 Plan ID"""
        import re
        import uuid
        match = re.search(r'\*\*Plan ID\*\*:\s*(\S+)', plan_content)
        if match:
            return match.group(1)
        # 如果 LLM 没有生成有效的 Plan ID，生成一个
        return str(uuid.uuid4())
