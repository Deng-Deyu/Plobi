"""
Agent 记忆 CRUD 操作
Phase 2: 数据持久化
"""

import aiosqlite
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json
from .db import get_db


@dataclass
class AgentMemory:
    key: str
    agent_id: str
    memory_key: str
    value: str
    category: str
    created_at: int


async def remember(
    agent_id: str,
    memory_key: str,
    value: str,
    category: str = "general"
) -> AgentMemory:
    """存储一条记忆"""
    db = await get_db()
    now = int(datetime.now().timestamp())
    key = f"{agent_id}:{memory_key}"
    
    await db.execute(
        """INSERT OR REPLACE INTO agent_memories 
           (key, agent_id, memory_key, value, category, created_at) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (key, agent_id, memory_key, value, category, now)
    )
    await db.commit()
    await db.close()
    
    return AgentMemory(
        key=key,
        agent_id=agent_id,
        memory_key=memory_key,
        value=value,
        category=category,
        created_at=now
    )


async def recall(
    agent_id: str,
    category: Optional[str] = None,
    limit: int = 50
) -> List[AgentMemory]:
    """检索记忆"""
    db = await get_db()
    
    if category:
        cursor = await db.execute(
            "SELECT key, agent_id, memory_key, value, category, created_at FROM agent_memories WHERE agent_id = ? AND category = ? ORDER BY created_at DESC LIMIT ?",
            (agent_id, category, limit)
        )
    else:
        cursor = await db.execute(
            "SELECT key, agent_id, memory_key, value, category, created_at FROM agent_memories WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
            (agent_id, limit)
        )
    
    rows = await cursor.fetchall()
    await db.close()
    
    return [
        AgentMemory(
            key=row[0],
            agent_id=row[1],
            memory_key=row[2],
            value=row[3],
            category=row[4],
            created_at=row[5]
        )
        for row in rows
    ]


async def get_context_injection(agent_id: str) -> str:
    """生成注入到 system_prompt 的记忆上下文"""
    memories = await recall(agent_id, limit=20)
    if not memories:
        return ""
    
    lines = [f"- {m.memory_key}: {m.value}" for m in memories]
    return "以下是你记忆中关于用户的信息：\n" + "\n".join(lines)


async def forget(agent_id: str, memory_key: str) -> bool:
    """删除特定记忆"""
    db = await get_db()
    key = f"{agent_id}:{memory_key}"
    cursor = await db.execute("DELETE FROM agent_memories WHERE key = ?", (key,))
    await db.commit()
    deleted = cursor.rowcount > 0
    await db.close()
    return deleted
