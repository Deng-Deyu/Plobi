"""
LangGraph 多 Agent 状态机
Phase 2: Agent 编排
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Literal
import operator
import json

from .researcher import ResearcherAgent
from .engineer import EngineerAgent
from .publisher import PublisherAgent
from .musician import MusicianAgent
from .videographer import VideographerAgent


class OrchestratorState(TypedDict):
    """全局任务状态，在所有 Agent 节点间传递"""
    session_id: str
    user_message: str
    plan_id: str
    plan_content: str
    messages: Annotated[list[dict], operator.add]
    active_agents: list[str]
    task_results: dict[str, str]
    status: Literal["planning", "dispatching", "running", "aggregating", "done", "error"]
    error: str | None


# 默认 Agent 配置（Phase 2: 简化版，Phase 3: 从数据库读取）
DEFAULT_AGENT_CONFIGS = {
    "researcher": {
        "name": "研究员",
        "persona": {"description": "研究员"},
        "model": {"provider": "deepseek", "model_id": "deepseek-chat", "temperature": 0.5, "max_tokens": 4096}
    },
    "engineer": {
        "name": "工程师",
        "persona": {"description": "工程师"},
        "model": {"provider": "deepseek", "model_id": "deepseek-coder", "temperature": 0.3, "max_tokens": 8192}
    },
    "publisher": {
        "name": "出版官",
        "persona": {"description": "出版官"},
        "model": {"provider": "anthropic", "model_id": "claude-opus-4-5", "temperature": 0.8, "max_tokens": 4096}
    },
    "musician": {
        "name": "音乐家",
        "persona": {"description": "音乐家"},
        "model": {"provider": "anthropic", "model_id": "claude-opus-4-5", "temperature": 0.8, "max_tokens": 4096}
    },
    "videographer": {
        "name": "剪辑师",
        "persona": {"description": "剪辑师"},
        "model": {"provider": "deepseek", "model_id": "deepseek-chat", "temperature": 0.7, "max_tokens": 4096}
    }
}


def build_orchestrator() -> StateGraph:
    """构建 LangGraph 状态机"""
    g = StateGraph(OrchestratorState)

    # 添加节点
    g.add_node("master_chat", master_chat_node)
    g.add_node("dispatch", dispatch_node)
    g.add_node("researcher", researcher_node)
    g.add_node("engineer", engineer_node)
    g.add_node("publisher", publisher_node)
    g.add_node("musician", musician_node)
    g.add_node("videographer", videographer_node)
    g.add_node("aggregate", aggregate_node)

    # 设置入口
    g.set_entry_point("master_chat")

    # Master 决定是否需要规划
    g.add_conditional_edges("master_chat", route_after_master, {
        "need_plan": "dispatch",
        "direct_reply": END,
    })

    # 分发后路由到对应子 Agent
    g.add_conditional_edges("dispatch", route_to_agents, {
        "researcher": "researcher",
        "engineer": "engineer",
        "publisher": "publisher",
        "musician": "musician",
        "videographer": "videographer",
        "aggregate": "aggregate",
    })

    # 所有子 Agent 完成后聚合
    for agent in ["researcher", "engineer", "publisher", "musician", "videographer"]:
        g.add_edge(agent, "aggregate")

    g.add_edge("aggregate", END)
    return g.compile()


# ─── 节点实现 ───────────────────────────────────────────────

async def master_chat_node(state: OrchestratorState) -> OrchestratorState:
    """Master Agent 对话节点：理解需求、生成 plan.md"""
    # 注意：此节点在 main.py 中通过 MasterAgent 直接处理
    # LangGraph 主要用于子 Agent 调度
    state["status"] = "planning"
    return state


async def dispatch_node(state: OrchestratorState) -> OrchestratorState:
    """分发任务到子 Agent"""
    state["status"] = "dispatching"
    # 根据 plan.md 决定激活哪些子 Agent
    # Phase 2: 暂时激活所有子 Agent
    state["active_agents"] = ["researcher", "engineer", "publisher", "musician", "videographer"]
    return state


async def researcher_node(state: OrchestratorState) -> OrchestratorState:
    """研究员节点"""
    agent = ResearcherAgent("researcher", DEFAULT_AGENT_CONFIGS["researcher"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    state["messages"].append({
        "role": "assistant",
        "agent_id": "researcher",
        "content": result
    })
    state["task_results"]["researcher"] = result
    return state


async def engineer_node(state: OrchestratorState) -> OrchestratorState:
    """工程师节点"""
    agent = EngineerAgent("engineer", DEFAULT_AGENT_CONFIGS["engineer"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    state["messages"].append({
        "role": "assistant",
        "agent_id": "engineer",
        "content": result
    })
    state["task_results"]["engineer"] = result
    return state


async def publisher_node(state: OrchestratorState) -> OrchestratorState:
    """出版官节点"""
    agent = PublisherAgent("publisher", DEFAULT_AGENT_CONFIGS["publisher"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    state["messages"].append({
        "role": "assistant",
        "agent_id": "publisher",
        "content": result
    })
    state["task_results"]["publisher"] = result
    return state


async def musician_node(state: OrchestratorState) -> OrchestratorState:
    """音乐家节点"""
    agent = MusicianAgent("musician", DEFAULT_AGENT_CONFIGS["musician"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    state["messages"].append({
        "role": "assistant",
        "agent_id": "musician",
        "content": result
    })
    state["task_results"]["musician"] = result
    return state


async def videographer_node(state: OrchestratorState) -> OrchestratorState:
    """剪辑师节点"""
    agent = VideographerAgent("videographer", DEFAULT_AGENT_CONFIGS["videographer"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    state["messages"].append({
        "role": "assistant",
        "agent_id": "videographer",
        "content": result
    })
    state["task_results"]["videographer"] = result
    return state


async def aggregate_node(state: OrchestratorState) -> OrchestratorState:
    """聚合所有子 Agent 结果"""
    state["status"] = "aggregating"
    summary = f"所有任务已完成：\n"
    for agent_id, result in state["task_results"].items():
        summary += f"- {agent_id}: {result[:100]}...\n"
    state["messages"].append({
        "role": "assistant",
        "agent_id": "master",
        "content": summary
    })
    state["status"] = "done"
    return state


# ─── 路由函数 ───────────────────────────────────────────────

def route_after_master(state: OrchestratorState) -> Literal["need_plan", "direct_reply"]:
    """Master 决定是否需要规划"""
    # Phase 2: 简单判断，Phase 3: LLM 决策
    if "复杂" in state["user_message"] or "任务" in state["user_message"]:
        return "need_plan"
    return "direct_reply"


def route_to_agents(state: OrchestratorState) -> Literal["researcher", "engineer", "publisher", "musician", "videographer", "aggregate"]:
    """路由到对应子 Agent"""
    # Phase 2: 简单轮询，Phase 3: 根据 plan.md 路由
    if not state["active_agents"]:
        return "aggregate"
    return state["active_agents"][0] if state["active_agents"] else "aggregate"
