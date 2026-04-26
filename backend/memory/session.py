"""
会话 CRUD 操作
Phase 2: 数据持久化
"""

import aiosqlite
from datetime import datetime
from typing import Optional, List
import json
from .db import get_db


class Session:
    id: str
    title: str
    preview: str
    primary_agent_id: str
    active_agent_ids: List[str]
    created_at: int
    updated_at: int


async def create_session(
    id: str,
    title: str,
    primary_agent_id: str = "master",
    active_agent_ids: Optional[List[str]] = None
) -> Session:
    """创建新会话"""
    db = await get_db()
    now = int(datetime.now().timestamp())
    active_ids = json.dumps(active_agent_ids or ["master"])
    
    await db.execute(
        "INSERT INTO sessions (id, title, preview, primary_agent_id, active_agent_ids, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id, title, "", primary_agent_id, active_ids, now, now)
    )
    await db.commit()
    await db.close()
    
    return Session(
        id=id,
        title=title,
        preview="",
        primary_agent_id=primary_agent_id,
        active_agent_ids=active_agent_ids or ["master"],
        created_at=now,
        updated_at=now
    )


async def get_session(session_id: str) -> Optional[Session]:
    """获取单个会话"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, title, preview, primary_agent_id, active_agent_ids, created_at, updated_at FROM sessions WHERE id = ?",
        (session_id,)
    )
    row = await cursor.fetchone()
    await db.close()
    
    if not row:
        return None
    
    return Session(
        id=row[0],
        title=row[1],
        preview=row[2],
        primary_agent_id=row[3],
        active_agent_ids=json.loads(row[4]),
        created_at=row[5],
        updated_at=row[6]
    )


async def list_sessions(limit: int = 50, offset: int = 0) -> List[Session]:
    """列出所有会话（按更新时间倒序）"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, title, preview, primary_agent_id, active_agent_ids, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    rows = await cursor.fetchall()
    await db.close()
    
    return [
        Session(
            id=row[0],
            title=row[1],
            preview=row[2],
            primary_agent_id=row[3],
            active_agent_ids=json.loads(row[4]),
            created_at=row[5],
            updated_at=row[6]
        )
        for row in rows
    ]


async def update_session(
    session_id: str,
    title: Optional[str] = None,
    preview: Optional[str] = None,
    active_agent_ids: Optional[List[str]] = None
) -> Optional[Session]:
    """更新会话"""
    db = await get_db()
    now = int(datetime.now().timestamp())
    
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if preview is not None:
        updates.append("preview = ?")
        params.append(preview)
    if active_agent_ids is not None:
        updates.append("active_agent_ids = ?")
        params.append(json.dumps(active_agent_ids))
    
    if not updates:
        await db.close()
        return await get_session(session_id)
    
    updates.append("updated_at = ?")
    params.append(now)
    params.append(session_id)
    
    await db.execute(
        f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
        params
    )
    await db.commit()
    await db.close()
    
    return await get_session(session_id)


async def delete_session(session_id: str) -> bool:
    """删除会话（级联删除关联消息）"""
    db = await get_db()
    cursor = await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    await db.commit()
    deleted = cursor.rowcount > 0
    await db.close()
    return deleted
