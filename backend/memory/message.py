"""
消息 CRUD 操作
Phase 2: 数据持久化
"""

import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
from .db import get_db


@dataclass
class Message:
    id: str
    session_id: str
    agent_id: str
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    attachments: List[Dict[str, Any]]
    plan_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: int


async def create_message(
    id: str,
    session_id: str,
    agent_id: str,
    role: str,
    content: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    plan_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Message:
    """创建新消息"""
    db = await get_db()
    now = int(datetime.now().timestamp())

    await db.execute(
        """INSERT INTO messages
           (id, session_id, agent_id, role, content, attachments, plan_id, metadata, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            id,
            session_id,
            agent_id,
            role,
            content,
            json.dumps(attachments or []),
            plan_id,
            json.dumps(metadata or {}),
            now
        )
    )

    # 更新会话的 preview 和 updated_at
    preview = content[:100] if content else ""
    await db.execute(
        "UPDATE sessions SET preview = ?, updated_at = ? WHERE id = ?",
        (preview, now, session_id)
    )

    await db.commit()
    await db.close()

    return Message(
        id=id,
        session_id=session_id,
        agent_id=agent_id,
        role=role,
        content=content,
        attachments=attachments or [],
        plan_id=plan_id,
        metadata=metadata or {},
        created_at=now
    )


async def get_message(message_id: str) -> Optional[Message]:
    """获取单条消息"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, session_id, agent_id, role, content, attachments, plan_id, metadata, created_at FROM messages WHERE id = ?",
        (message_id,)
    )
    row = await cursor.fetchone()
    await db.close()
    
    if not row:
        return None
    
    return Message(
        id=row[0],
        session_id=row[1],
        agent_id=row[2],
        role=row[3],
        content=row[4],
        attachments=json.loads(row[5]),
        plan_id=row[6],
        metadata=json.loads(row[7]),
        created_at=row[8]
    )


async def list_messages(
    session_id: str,
    limit: int = 100,
    offset: int = 0
) -> List[Message]:
    """列出会话的所有消息（按时间正序）"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, session_id, agent_id, role, content, attachments, plan_id, metadata, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
        (session_id, limit, offset)
    )
    rows = await cursor.fetchall()
    await db.close()
    
    return [
        Message(
            id=row[0],
            session_id=row[1],
            agent_id=row[2],
            role=row[3],
            content=row[4],
            attachments=json.loads(row[5]),
            plan_id=row[6],
            metadata=json.loads(row[7]),
            created_at=row[8]
        )
        for row in rows
    ]


async def update_message(
    message_id: str,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Message]:
    """更新消息内容（用于流式更新）"""
    db = await get_db()
    
    updates = []
    params = []
    
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))
    
    if not updates:
        await db.close()
        return await get_message(message_id)
    
    params.append(message_id)
    
    await db.execute(
        f"UPDATE messages SET {', '.join(updates)} WHERE id = ?",
        params
    )
    await db.commit()
    await db.close()
    
    return await get_message(message_id)


async def delete_message(message_id: str) -> bool:
    """删除消息"""
    db = await get_db()
    cursor = await db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    await db.commit()
    deleted = cursor.rowcount > 0
    await db.close()
    return deleted
