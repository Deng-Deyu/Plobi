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
    g.add_node("dispatch", dispatch_node)
    g.add_node("researcher", researcher_node)
    g.add_node("engineer", engineer_node)
    g.add_node("publisher", publisher_node)
    g.add_node("musician", musician_node)
    g.add_node("videographer", videographer_node)
    g.add_node("aggregate", aggregate_node)

    # 取消 master_chat_node，直接从 dispatch 开始
    g.set_entry_point("dispatch")

    # 分发后路由到对应子 Agent 或聚合
    g.add_conditional_edges("dispatch", route_to_next_agent)

    # 所有子 Agent 完成后回到 dispatch 调度下一个
    for agent in ["researcher", "engineer", "publisher", "musician", "videographer"]:
        g.add_edge(agent, "dispatch")

    g.add_edge("aggregate", END)
    return g.compile()


# ─── 节点实现 ───────────────────────────────────────────────

async def dispatch_node(state: OrchestratorState) -> OrchestratorState:
    """分发任务到子 Agent"""
    import re
    state["status"] = "dispatching"
    
    # 如果还没有解析过 plan，解析它
    if not state.get("active_agents"):
        plan_content = state.get("plan_content", "")
        # 从 markdown 中正则提取所有的 "**负责 Agent**: xxxx"
        matches = re.findall(r'\*\*负责 Agent\*\*:?\s*([a-zA-Z0-9_]+)', plan_content)
        valid_agents = [m.lower().strip() for m in matches if m.lower().strip() in DEFAULT_AGENT_CONFIGS]
        # 去重但保持顺序
        seen = set()
        active_agents = []
        for a in valid_agents:
            if a not in seen:
                active_agents.append(a)
                seen.add(a)
        
        state["active_agents"] = active_agents
        
    return state


async def researcher_node(state: OrchestratorState) -> dict:
    """研究员节点"""
    agent = ResearcherAgent("researcher", DEFAULT_AGENT_CONFIGS["researcher"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    new_msg = {
        "role": "assistant",
        "agent_id": "researcher",
        "content": result
    }
    task_results = state.get("task_results", {}).copy()
    task_results["researcher"] = result
    return {"messages": [new_msg], "task_results": task_results}


async def engineer_node(state: OrchestratorState) -> dict:
    """工程师节点"""
    agent = EngineerAgent("engineer", DEFAULT_AGENT_CONFIGS["engineer"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    new_msg = {
        "role": "assistant",
        "agent_id": "engineer",
        "content": result
    }
    task_results = state.get("task_results", {}).copy()
    task_results["engineer"] = result
    return {"messages": [new_msg], "task_results": task_results}


async def publisher_node(state: OrchestratorState) -> dict:
    """出版官节点"""
    agent = PublisherAgent("publisher", DEFAULT_AGENT_CONFIGS["publisher"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    new_msg = {
        "role": "assistant",
        "agent_id": "publisher",
        "content": result
    }
    task_results = state.get("task_results", {}).copy()
    task_results["publisher"] = result
    return {"messages": [new_msg], "task_results": task_results}


async def musician_node(state: OrchestratorState) -> dict:
    """音乐家节点"""
    agent = MusicianAgent("musician", DEFAULT_AGENT_CONFIGS["musician"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    new_msg = {
        "role": "assistant",
        "agent_id": "musician",
        "content": result
    }
    task_results = state.get("task_results", {}).copy()
    task_results["musician"] = result
    return {"messages": [new_msg], "task_results": task_results}


async def videographer_node(state: OrchestratorState) -> dict:
    """剪辑师节点"""
    agent = VideographerAgent("videographer", DEFAULT_AGENT_CONFIGS["videographer"])
    result = await agent.execute(
        task_description=state["user_message"],
        input_data=state.get("plan_content", "")
    )
    new_msg = {
        "role": "assistant",
        "agent_id": "videographer",
        "content": result
    }
    task_results = state.get("task_results", {}).copy()
    task_results["videographer"] = result
    return {"messages": [new_msg], "task_results": task_results}


async def aggregate_node(state: OrchestratorState) -> dict:
    """聚合所有子 Agent 结果"""
    summary = f"所有任务已完成：\n"
    for agent_id, result in state.get("task_results", {}).items():
        summary += f"- {agent_id}: {result[:100]}...\n"
    new_msg = {
        "role": "assistant",
        "agent_id": "master",
        "content": summary
    }
    return {"messages": [new_msg], "status": "done"}


# ─── 路由函数 ───────────────────────────────────────────────

# ─── 路由函数 ───────────────────────────────────────────────

def route_to_next_agent(state: OrchestratorState) -> Literal["researcher", "engineer", "publisher", "musician", "videographer", "aggregate"]:
    """路由到下一个子 Agent"""
    if not state.get("active_agents"):
        return "aggregate"
    
    # 获取下一个 agent
    next_agent = state["active_agents"][0]
    
    # 状态不在这里更新，LangGraph 路由函数应该是纯函数，不应修改 state
    # state 的更新必须在 node 中进行。
    # 既然如此，我们要么在 dispatch_node 中就把它 pop 掉并返回（但我们需要知道本次调度谁）
    # 其实如果我们在 dispatch_node 中：
    # state["current_agent"] = next_agent
    # state["active_agents"] = active_agents[1:]
    # 就可以，然后在路由函数里 return state["current_agent"]。
    
    # 或者就根据 task_results 判断：已经有结果的说明执行过了
    # 这也是一个纯函数的方式
    for agent in state["active_agents"]:
        if agent not in state.get("task_results", {}):
            return agent
            
    return "aggregate"
