"""
SQLite 数据库初始化与连接池
Phase 2: 数据持久化
"""

import aiosqlite
from pathlib import Path
from typing import Optional
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "plobi.db"


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接（连接池由 aiosqlite 内部管理）"""
    return await aiosqlite.connect(DB_PATH)


async def init_db():
    """初始化数据库表结构"""
    db = await get_db()
    
    # 会话表
    await db.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            preview TEXT DEFAULT '',
            primary_agent_id TEXT NOT NULL DEFAULT 'master',
            active_agent_ids TEXT NOT NULL DEFAULT '[]',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
    
    # 消息表
    await db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            agent_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
            content TEXT NOT NULL,
            attachments TEXT DEFAULT '[]',
            plan_id TEXT,
            metadata TEXT DEFAULT '{}',
            created_at INTEGER NOT NULL
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at)")
    
    # Agent 配置表
    await db.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            avatar_json TEXT NOT NULL,
            persona_json TEXT NOT NULL,
            model_json TEXT NOT NULL,
            skills TEXT DEFAULT '[]',
            mcp_servers TEXT DEFAULT '[]',
            is_active INTEGER DEFAULT 1,
            created_at INTEGER NOT NULL
        )
    """)
    
    # Agent 记忆表
    await db.execute("""
        CREATE TABLE IF NOT EXISTS agent_memories (
            key TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            memory_key TEXT NOT NULL,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at INTEGER NOT NULL
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_agent_memories_agent ON agent_memories(agent_id, category)")
    
    # 任务表
    await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','running','done','error')),
            description TEXT NOT NULL,
            result TEXT,
            output_files TEXT DEFAULT '[]',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_plan ON tasks(plan_id)")
    
    await db.commit()
    await db.close()
    print(f"[DB] Database initialized at {DB_PATH}")


async def seed_default_agents():
    """插入默认 Agent 配置"""
    db = await get_db()
    
    default_agents = [
        {
            "id": "master",
            "name": "Master",
            "avatar_json": json.dumps({"type": "emoji", "value": "🧠"}),
            "persona_json": json.dumps({
                "description": "中枢主控，负责与用户对话、理解需求、生成 plan.md 并调度子 Agent",
                "tone": "专业、主动、有明确人格",
                "greeting": "你好！我是 Plobi 的 Master Agent，有什么我可以帮你的？"
            }),
            "model_json": json.dumps({
                "provider": "deepseek",
                "model_id": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4096
            }),
            "skills": json.dumps(["planning", "dispatching", "aggregation"]),
            "mcp_servers": json.dumps([])
        },
        {
            "id": "researcher",
            "name": "研究员",
            "avatar_json": json.dumps({"type": "emoji", "value": "🔬"}),
            "persona_json": json.dumps({
                "description": "负责新技术/新消息收集、网络检索、信息整理",
                "tone": "严谨、数据驱动",
                "greeting": "我是研究员，帮你收集和分析信息。"
            }),
            "model_json": json.dumps({
                "provider": "deepseek",
                "model_id": "deepseek-chat",
                "temperature": 0.5,
                "max_tokens": 4096
            }),
            "skills": json.dumps(["web_search", "data_analysis", "report_writing"]),
            "mcp_servers": json.dumps(["brave-search", "fetch"])
        },
        {
            "id": "engineer",
            "name": "工程师",
            "avatar_json": json.dumps({"type": "emoji", "value": "⚙️"}),
            "persona_json": json.dumps({
                "description": "负责建模软件操控、代码生成执行、3D/CAD/科学计算",
                "tone": "技术导向、精确",
                "greeting": "我是工程师，帮你处理技术实现。"
            }),
            "model_json": json.dumps({
                "provider": "deepseek",
                "model_id": "deepseek-coder",
                "temperature": 0.3,
                "max_tokens": 8192
            }),
            "skills": json.dumps(["code_generation", "cli_execution", "3d_modeling"]),
            "mcp_servers": json.dumps(["filesystem"])
        },
        {
            "id": "publisher",
            "name": "出版官",
            "avatar_json": json.dumps({"type": "emoji", "value": "📝"}),
            "persona_json": json.dumps({
                "description": "负责 PPT/课程/科研论文/技术文档制作",
                "tone": "专业、注重格式",
                "greeting": "我是出版官，帮你制作文档和演示文稿。"
            }),
            "model_json": json.dumps({
                "provider": "anthropic",
                "model_id": "claude-opus-4-5",
                "temperature": 0.8,
                "max_tokens": 4096
            }),
            "skills": json.dumps(["ppt_generation", "latex", "document_formatting"]),
            "mcp_servers": json.dumps([])
        },
        {
            "id": "musician",
            "name": "音乐家",
            "avatar_json": json.dumps({"type": "emoji", "value": "🎵"}),
            "persona_json": json.dumps({
                "description": "负责音频分析、五线谱/六线谱制作、Guitar Pro 适配",
                "tone": "热情、专业",
                "greeting": "我是音乐家，帮你处理音乐相关任务。"
            }),
            "model_json": json.dumps({
                "provider": "anthropic",
                "model_id": "claude-opus-4-5",
                "temperature": 0.8,
                "max_tokens": 4096
            }),
            "skills": json.dumps(["audio_analysis", "music_theory", "score_generation"]),
            "mcp_servers": json.dumps([])
        },
        {
            "id": "videographer",
            "name": "剪辑师",
            "avatar_json": json.dumps({"type": "emoji", "value": "🎬"}),
            "persona_json": json.dumps({
                "description": "负责视频剪辑、字幕生成、视频生成",
                "tone": "创意、视觉导向",
                "greeting": "我是剪辑师，帮你处理视频内容。"
            }),
            "model_json": json.dumps({
                "provider": "deepseek",
                "model_id": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4096
            }),
            "skills": json.dumps(["video_editing", "subtitle_generation", "video_generation"]),
            "mcp_servers": json.dumps([])
        }
    ]
    
    for agent in default_agents:
        await db.execute("""
            INSERT OR REPLACE INTO agents 
            (id, name, avatar_json, persona_json, model_json, skills, mcp_servers, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, strftime('%s', 'now'))
        """, (
            agent["id"],
            agent["name"],
            agent["avatar_json"],
            agent["persona_json"],
            agent["model_json"],
            agent["skills"],
            agent["mcp_servers"]
        ))
    
    await db.commit()
    await db.close()
    print("[DB] Default agents seeded")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    asyncio.run(seed_default_agents())
