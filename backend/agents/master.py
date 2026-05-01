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

你的职责：
1. 与用户直接对话，追问细节，澄清需求
2. 理解用户需求，判断是否需要调用子 Agent
3. 生成标准化的 plan.md 任务书
4. 将任务分发给对应子 Agent
5. 聚合子 Agent 成果，向用户汇报

对话风格：
- 主动追问关键信息（截止时间？格式要求？受众？）
- 用第一人称，有明确名字和人格
- 汇报时引用子 Agent 名称
- 简洁专业，避免冗余

决策规则：
- 如果用户需求简单（如简单问答），直接回复
- 如果用户需求复杂（如需要研究、创作、技术实现），生成 plan.md 并调度子 Agent
"""
    
    async def chat(
        self,
        user_message: str,
        session_id: str,
        agent_config: dict,
        memory_context: str = ""
    ) -> dict:
        """与用户对话"""
        # 构建系统提示
        system_content = self.system_prompt
        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_message)
        ]
        
        # 调用 LLM
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
        
        # 判断是否需要规划（简化版，Phase 3 用 LLM 决策）
        needs_plan = self._needs_plan(user_message, response)
        
        return {
            "content": response,
            "needs_plan": needs_plan,
            "agent_id": "master"
        }
    
    def _needs_plan(self, user_message: str, ai_response: str) -> bool:
        """判断是否需要生成 plan.md"""
        # 简化规则：如果用户消息包含特定关键词，需要规划
        plan_keywords = [
            "研究", "分析", "生成", "制作", "实现", "设计",
            "任务", "项目", "报告", "文档", "PPT", "视频",
            "音乐", "音频", "代码", "建模", "剪辑"
        ]
        return any(keyword in user_message for keyword in plan_keywords)
    
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
