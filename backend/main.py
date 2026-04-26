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


# ─── DeepSeek SSE Stream ───────────────────────────────────

async def stream_deepseek(prompt: str, queue: asyncio.Queue):
    """Stream tokens from DeepSeek API and push to SSE queue."""
    if not DEEPSEEK_API_KEY:
        await queue.put({"type": "token", "content": "⚠️ 未配置 DEEPSEEK_API_KEY，请在 .env 中设置"})
        await queue.put({"type": "done"})
        return

    system_prompt = (
        "你是 Plobi Agent 的 Master Agent（中枢主控）。"
        "你负责与用户对话、理解需求、追问细节。"
        "回复使用中文，风格简洁专业。"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
        "max_tokens": 4096,
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code != 200:
                    error_text = await resp.aread()
                    await queue.put({
                        "type": "error",
                        "message": f"DeepSeek API 错误 ({resp.status_code}): {error_text.decode()[:200]}",
                    })
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            await queue.put({"type": "token", "content": content})
                    except json.JSONDecodeError:
                        continue

        await queue.put({"type": "done"})

    except Exception as e:
        await queue.put({"type": "error", "message": str(e)})


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
            # 保存用户消息到数据库
            await create_message(
                id=body.message_id,
                session_id=body.session_id,
                agent_id="user",
                role="user",
                content=body.prompt,
                attachments=body.attachment_ids
            )
            
            # 调用 Master Agent
            agent_config = {
                "model": {
                    "provider": "deepseek",
                    "model_id": "deepseek-chat",
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
            }
            
            result = await master_agent.chat(
                user_message=body.prompt,
                session_id=body.session_id,
                agent_config=agent_config
            )
            
            # 流式输出 Master 响应
            for char in result["content"]:
                await queue.put({"type": "token", "content": char})
                await asyncio.sleep(0.01)  # 模拟流式
            
            # 如果需要规划，生成 plan.md
            if result["needs_plan"]:
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
            
            await queue.put({"type": "done"})
            
        except Exception as e:
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


# ─── App ───────────────────────────────────────────────────

app = FastAPI(title="Plobi Agent Backend", version="0.2.0")


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await init_db()
    await seed_default_agents()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(session_router)
app.include_router(files_router)


@app.get("/health")
async def health():
    return {"status": "ok", "api_key_configured": bool(DEEPSEEK_API_KEY)}


if __name__ == "__main__":
    import uvicorn
    print(f"[Plobi Backend] Starting on http://127.0.0.1:{BACKEND_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT)
