"""
Plobi Agent Backend — FastAPI + SSE
Phase 2: SQLite 持久化 + LangGraph 集成
"""

import os
import json
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

from memory.db import init_db, seed_default_agents
from memory.session import create_session, get_session, list_sessions, update_session, delete_session
from memory.message import create_message, list_messages, update_message
from agents.graph import build_orchestrator
from agents.master import MasterAgent
from planner.plan_generator import PlanGenerator
from api.files import router as files_router
from api.plugins import router as plugins_router
from api.cli import router as cli_router
from api.exports import router as exports_router
from api.agents import router as agents_router
from api.sandbox import router as sandbox_router
from mcpclient.client import mcp_manager

load_dotenv()

# ─── Config ────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)

BACKEND_PORT = int(os.getenv("PLOBI_BACKEND_PORT", "52731"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# ─── SSE Queue Registry ────────────────────────────────────

_queues: dict[str, asyncio.Queue] = {}

# ─── Global Agents ───────────────────────────────────────────

orchestrator = build_orchestrator()
master_agent = MasterAgent()
plan_generator = PlanGenerator(WORKSPACE_DIR)


def get_or_create_queue(session_id: str, message_id: str) -> asyncio.Queue:
    key = f"{session_id}:{message_id}"
    if key not in _queues:
        _queues[key] = asyncio.Queue()
    return _queues[key]


# ─── Pydantic Models ───────────────────────────────────────

class SendMessageRequest(BaseModel):
    session_id: str
    agent_id: str
    message_id: str
    prompt: str
    attachment_ids: list[str] = []


class SessionInfo(BaseModel):
    id: str
    title: str
    preview: str
    created_at: float
    updated_at: float


# ─── Routers ───────────────────────────────────────────────

chat_router = APIRouter(prefix="/chat", tags=["chat"])
session_router = APIRouter(prefix="/sessions", tags=["sessions"])


@chat_router.get("/stream")
async def stream_chat(session_id: str, agent_id: str, message_id: str):
    """SSE stream endpoint: frontend connects here, then POSTs /send."""

    async def generate():
        queue = get_or_create_queue(session_id, message_id)
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=120)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") in ("done", "error"):
                    break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'timeout'})}\n\n"
        finally:
            # Cleanup
            key = f"{session_id}:{message_id}"
            _queues.pop(key, None)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@chat_router.post("/send")
async def send_message(body: SendMessageRequest):
    """Receive user message, start LangGraph orchestrator."""
    queue = get_or_create_queue(body.session_id, body.message_id)

    async def run_graph():
        try:
            # 确保会话存在（防止外键约束失败）
            existing = await get_session(body.session_id)
            if not existing:
                await create_session(body.session_id, "新对话")

            # 保存用户消息到数据库
            await create_message(
                id=body.message_id,
                session_id=body.session_id,
                agent_id="user",
                role="user",
                content=body.prompt,
                attachments=body.attachment_ids
            )

            # 调用 Master Agent (流式)
            agent_config = {
                "model": {
                    "provider": "deepseek",
                    "model_id": "deepseek-chat",
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
            }

            needs_plan = False
            accumulated_content = ""
            async for chunk_info in master_agent.astream_chat(
                user_message=body.prompt,
                session_id=body.session_id,
                agent_config=agent_config
            ):
                if chunk_info["type"] == "token":
                    accumulated_content += chunk_info["content"]
                    await queue.put({"type": "token", "content": chunk_info["content"]})
                elif chunk_info["type"] == "done":
                    needs_plan = chunk_info.get("needs_plan", False)
            
            # 如果需要规划，生成 plan.md
            if needs_plan:
                plan_result = await master_agent.generate_plan(
                    user_message=body.prompt,
                    session_id=body.session_id,
                    agent_config=agent_config
                )
                await queue.put({
                    "type": "plan_created",
                    "plan_id": plan_result["plan_id"],
                    "plan_content": plan_result["plan_content"]
                })
                
                # 开始执行 LangGraph
                from agents.graph import build_orchestrator
                graph = build_orchestrator()
                initial_state = {
                    "session_id": body.session_id,
                    "user_message": body.prompt,
                    "plan_id": plan_result["plan_id"],
                    "plan_content": plan_result["plan_content"],
                    "messages": [],
                    "active_agents": [],
                    "task_results": {},
                    "status": "dispatching",
                    "error": None
                }
                
                async for event in graph.astream(initial_state):
                    for node_name, state_update in event.items():
                        if node_name in ["dispatch", "__start__"]:
                            continue
                        
                        # 推送子 Agent 进度
                        await queue.put({
                            "type": "agent_progress",
                            "agent_id": node_name,
                            "status": "done"
                        })
                        
                        # 如果有新消息，保存到数据库并推送给前端
                        if "messages" in state_update and state_update["messages"]:
                            latest_msg = state_update["messages"][-1]
                            content = latest_msg["content"]
                            await queue.put({
                                "type": "agent_message",
                                "agent_id": latest_msg["agent_id"],
                                "content": content
                            })
                            # 检测文件产出（匹配 [文件已保存] path）
                            import re
                            file_match = re.search(r'\[文件已保存\]\s*(.+?)(?:\n|$)', content)
                            if file_match:
                                file_path = file_match.group(1).strip()
                                await queue.put({
                                    "type": "file_output",
                                    "agent_id": latest_msg["agent_id"],
                                    "filePath": file_path
                                })
                            # 检测 SANDBOX 代码块（工程师 / 音乐家 / 剪辑师 Agent）
                            sandbox_matches = re.findall(r'<!-- SANDBOX:(\w+) -->\n?(.*?)\n?<!-- /SANDBOX -->', content, re.DOTALL)
                            if sandbox_matches:
                                for lang, code in sandbox_matches:
                                    try:
                                        from api.sandbox import propose_execution, CodeExecutionRequest
                                        proposal = await propose_execution(CodeExecutionRequest(
                                            code=code.strip(),
                                            language=lang,
                                            description=f"{node_name} 提交的代码",
                                            agent_id=node_name,
                                            session_id=body.session_id
                                        ))
                                        await queue.put({
                                            "type": "agent_message",
                                            "agent_id": "system",
                                            "content": f"[沙盒执行] 代码已提交，等待用户确认。执行ID: {proposal['execution_id']}"
                                        })
                                    except Exception as e:
                                        await queue.put({
                                            "type": "agent_message",
                                            "agent_id": "system",
                                            "content": f"[沙盒执行] 提交失败: {e}"
                                        })
                            # 保存到数据库
                            await create_message(
                                id=f"{body.message_id}_{node_name}",
                                session_id=body.session_id,
                                agent_id=latest_msg["agent_id"],
                                role="assistant",
                                content=content,
                            )
            
            await queue.put({"type": "done"})
            
            # 保存 AI 回复到数据库
            ai_msg_id = f"{body.message_id}_reply"
            await create_message(
                id=ai_msg_id,
                session_id=body.session_id,
                agent_id="master",
                role="assistant",
                content=accumulated_content,
            )
            
            # 自动更新会话标题（第一条消息时）
            existing_msgs = await list_messages(body.session_id)
            if len(existing_msgs) <= 2:  # Only user msg + assistant msg
                # Use first 20 chars of user message as title
                title = body.prompt[:20]
                if len(body.prompt) > 20:
                    title += "..."
                await update_session(body.session_id, title=title)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await queue.put({"type": "error", "message": str(e)})

    asyncio.create_task(run_graph())
    return {"status": "ok"}


# ─── Session CRUD (SQLite) ──


@session_router.get("")
async def list_sessions_api():
    sessions = await list_sessions()
    return [
        {
            "id": s.id,
            "title": s.title,
            "preview": s.preview,
            "primary_agent_id": s.primary_agent_id,
            "active_agent_ids": s.active_agent_ids,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in sessions
    ]


@session_router.post("")
async def create_session_api():
    sid = str(uuid.uuid4())
    session = await create_session(sid, f"新对话")
    return {
        "id": session.id,
        "title": session.title,
        "preview": session.preview,
        "primary_agent_id": session.primary_agent_id,
        "active_agent_ids": session.active_agent_ids,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@session_router.get("/{session_id}")
async def get_session_api(session_id: str):
    session = await get_session(session_id)
    if not session:
        return {"error": "not found"}
    return {
        "id": session.id,
        "title": session.title,
        "preview": session.preview,
        "primary_agent_id": session.primary_agent_id,
        "active_agent_ids": session.active_agent_ids,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@session_router.delete("/{session_id}")
async def delete_session_api(session_id: str):
    deleted = await delete_session(session_id)
    return {"status": "ok" if deleted else "not found"}


@session_router.get("/{session_id}/messages")
async def list_session_messages(session_id: str):
    """获取会话的所有消息"""
    msgs = await list_messages(session_id)
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "agent_id": m.agent_id,
            "role": m.role,
            "content": m.content,
            "attachments": m.attachments,
            "plan_id": m.plan_id,
            "metadata": m.metadata,
            "created_at": m.created_at,
        }
        for m in msgs
    ]


@session_router.patch("/{session_id}")
async def patch_session(session_id: str, body: dict):
    """更新会话（标题、预览等）"""
    updated = await update_session(
        session_id,
        title=body.get("title"),
        preview=body.get("preview"),
    )
    if not updated:
        return {"error": "not found"}
    return {
        "id": updated.id,
        "title": updated.title,
        "preview": updated.preview,
        "primary_agent_id": updated.primary_agent_id,
        "active_agent_ids": updated.active_agent_ids,
        "created_at": updated.created_at,
        "updated_at": updated.updated_at,
    }


# ─── App ───────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    await init_db()
    await seed_default_agents()
    yield
    # Shutdown: 关闭所有 MCP 连接
    await mcp_manager.close_all()

app = FastAPI(title="Plobi Agent Backend", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost", "https://tauri.localhost", "http://tauri.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(session_router)
app.include_router(files_router)
app.include_router(plugins_router)
app.include_router(cli_router)
app.include_router(exports_router)
app.include_router(agents_router)
app.include_router(sandbox_router)


@app.get("/health")
async def health():
    return {"status": "ok", "api_key_configured": bool(DEEPSEEK_API_KEY)}


if __name__ == "__main__":
    import uvicorn
    print(f"[Plobi Backend] Starting on http://127.0.0.1:{BACKEND_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT)
