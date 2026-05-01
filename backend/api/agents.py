"""
Agent 配置与记忆 API 端点
Phase 4: Agent 配置界面 + 记忆系统
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json

from memory.db import get_db
from memory.agent_memory import remember, recall, forget

router = APIRouter(prefix="/agents", tags=["agents"])


# ─── Pydantic Models ──────────────────────────────────────

class AvatarConfig(BaseModel):
    type: str = "emoji"  # emoji | url | initials
    value: str = "🤖"

class PersonaConfig(BaseModel):
    description: str = ""
    tone: str = "专业"
    greeting: str = ""

class ModelConfig(BaseModel):
    provider: str = "deepseek"
    model_id: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    avatar: Optional[AvatarConfig] = None
    persona: Optional[PersonaConfig] = None
    model: Optional[ModelConfig] = None
    skills: Optional[List[str]] = None
    mcp_servers: Optional[List[str]] = None
    is_active: Optional[bool] = None

class MemoryCreateRequest(BaseModel):
    memory_key: str
    value: str
    category: str = "general"

class MemoryUpdateRequest(BaseModel):
    value: str
    category: Optional[str] = None

class MemoryDeleteRequest(BaseModel):
    memory_key: str


# ─── Agent CRUD ───────────────────────────────────────────

@router.get("")
async def list_agents():
    """列出所有 Agent 配置"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, name, avatar_json, persona_json, model_json, skills, mcp_servers, is_active, created_at FROM agents ORDER BY id"
    )
    rows = await cursor.fetchall()
    await db.close()

    agents = []
    for row in rows:
        agents.append({
            "id": row[0],
            "name": row[1],
            "avatar": json.loads(row[2]),
            "persona": json.loads(row[3]),
            "model": json.loads(row[4]),
            "skills": json.loads(row[5]),
            "mcp_servers": json.loads(row[6]),
            "is_active": bool(row[7]),
            "created_at": row[8],
        })
    return agents


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """获取单个 Agent 配置"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, name, avatar_json, persona_json, model_json, skills, mcp_servers, is_active, created_at FROM agents WHERE id = ?",
        (agent_id,)
    )
    row = await cursor.fetchone()
    await db.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    return {
        "id": row[0],
        "name": row[1],
        "avatar": json.loads(row[2]),
        "persona": json.loads(row[3]),
        "model": json.loads(row[4]),
        "skills": json.loads(row[5]),
        "mcp_servers": json.loads(row[6]),
        "is_active": bool(row[7]),
        "created_at": row[8],
    }


@router.put("/{agent_id}")
async def update_agent(agent_id: str, body: UpdateAgentRequest):
    """更新 Agent 配置"""
    db = await get_db()

    # Check agent exists
    cursor = await db.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
    if not await cursor.fetchone():
        await db.close()
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    # Build update query dynamically
    updates = []
    values = []

    if body.name is not None:
        updates.append("name = ?")
        values.append(body.name)

    if body.avatar is not None:
        updates.append("avatar_json = ?")
        values.append(json.dumps(body.avatar.model_dump()))

    if body.persona is not None:
        updates.append("persona_json = ?")
        values.append(json.dumps(body.persona.model_dump()))

    if body.model is not None:
        updates.append("model_json = ?")
        values.append(json.dumps(body.model.model_dump()))

    if body.skills is not None:
        updates.append("skills = ?")
        values.append(json.dumps(body.skills))

    if body.mcp_servers is not None:
        updates.append("mcp_servers = ?")
        values.append(json.dumps(body.mcp_servers))

    if body.is_active is not None:
        updates.append("is_active = ?")
        values.append(1 if body.is_active else 0)

    if not updates:
        await db.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(agent_id)
    await db.execute(
        f"UPDATE agents SET {', '.join(updates)} WHERE id = ?",
        values
    )
    await db.commit()
    await db.close()

    return {"status": "ok", "agent_id": agent_id}


# ─── Agent Memory CRUD ────────────────────────────────────

@router.get("/{agent_id}/memories")
async def list_agent_memories(agent_id: str, category: Optional[str] = None):
    """获取 Agent 的记忆列表"""
    memories = await recall(agent_id, category=category)
    return [
        {
            "key": m.key,
            "agent_id": m.agent_id,
            "memory_key": m.memory_key,
            "value": m.value,
            "category": m.category,
            "created_at": m.created_at,
        }
        for m in memories
    ]


@router.post("/{agent_id}/memories")
async def create_agent_memory(agent_id: str, body: MemoryCreateRequest):
    """添加一条 Agent 记忆"""
    result = await remember(
        agent_id=agent_id,
        memory_key=body.memory_key,
        value=body.value,
        category=body.category,
    )
    return {
        "status": "ok",
        "key": result.key,
    }


@router.delete("/{agent_id}/memories")
async def delete_agent_memory(agent_id: str, body: MemoryDeleteRequest):
    """删除一条 Agent 记忆"""
    deleted = await forget(agent_id=agent_id, memory_key=body.memory_key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "ok"}
