# PLOBI AGENT — 工程蓝图 V2.0

> **本文档用途**：项目根目录唯一权威技术参考。供本地 AI 编程工具（Cursor、Continue、Copilot 等）在每次开发会话开始时读取，确保工程决策的连续性与一致性。**开发者每次提问前必须将本文件附加到上下文。**
>
> **版本**：V2.0（从 V1.0 全面升版，整合全部用户需求）
> **最后更新**：2026-04-25
> **当前阶段**：Phase 1 — 脚手架搭建
> **开发者**：单人开发，所有架构决策以「一个人能实现」为上限

---

## 〇、快速索引

| 章节 | 内容 |
|------|------|
| 一 | 项目定位与核心愿景 |
| 二 | 技术栈决策（锁定，不可随意变更） |
| 三 | 目录结构 |
| 四 | 交互架构：双轨 + 群聊式 Agent 面板 |
| 五 | Master Agent 与子 Agent 分工规范 |
| 六 | Agent 配置系统（头像/人格/记忆/模型/MCP） |
| 七 | 核心模块实现规范（含代码模板） |
| 八 | 多模态输入规范（文本/文件/图片/音频） |
| 九 | MCP 与插件扩展系统 |
| 十 | 本地电脑操控规范（CLI 优先 + 沙盒） |
| 十一 | plan.md 任务编排协议 |
| 十二 | 数据库 Schema |
| 十三 | API 接口规范 |
| 十四 | Token 消耗优化策略 |
| 十五 | 云端部署预留设计 |
| 十六 | UI/UX 设计规范 |
| 十七 | 打包发行规范 |
| 十八 | 开发里程碑 |
| 十九 | 工程纪律（AI 工具必读） |

---

## 一、项目定位与核心愿景

**项目名**：Plobi Agent
**本质**：一个以群聊式多 Agent 协作为核心体验、可打包发行的跨平台桌面 AI 客户端。

### 核心体验目标（按优先级）

1. **群聊式 Agent 面板** —— 主界面像群聊，Master Agent 和子 Agent 各有独立卡片与消息气泡，可点开卡片查看进度或直接对话
2. **Master → 子 Agent 任务流** —— 用户与 Master 对话，Master 生成 `plan.md` 并自动下发任务至对应子 Agent
3. **流式打字机输出** —— 所有 Agent 响应逐字渲染，无卡顿
4. **双轨交互** —— `Alt+/` 极速浮窗（发送后跳转至 Master Agent 对话）+ 全景主控台
5. **多模态输入** —— 支持文本、文档（PDF/Word/MD）、图片、音频文件
6. **全 Agent 本地电脑权限** —— CLI 优先，文件形式交付任务成果
7. **Agent 深度自定义** —— 每个 Agent 独立配置：头像、名称、人格、记忆、模型、Skill、MCP
8. **插件生态** —— 支持自主安装插件扩展功能
9. **高可迭代性** —— 模块解耦，插件化架构，云端部署预留

### 绝对不做

- 不用 Gradio、Streamlit 任何 Python Web UI 框架渲染主界面
- 不做 Web 部署（当前阶段纯桌面，云端为未来预留）
- 不引入 Docker（目标是单一安装包）

---

## 二、技术栈决策（最终方案，不可随意变更）

### 2.1 完整技术栈

```
┌──────────────────────────────────────────────────────────┐
│  前端渲染层                                               │
│    框架        React 18 + TypeScript + Vite              │
│    UI 组件     shadcn/ui + Tailwind CSS 3                │
│    状态管理    Zustand 4                                  │
│    路由        React Router v6（多页面：主控台/设置/插件）│
│    Markdown    react-markdown + remark-gfm + remark-math │
│    代码高亮    Shiki（rehype-shiki）                      │
│    数学公式    rehype-katex + katex                       │
│    虚拟滚动    @tanstack/react-virtual（长消息列表）      │
│    文件预览    react-pdf（PDF）、mime-type 路由           │
├──────────────────────────────────────────────────────────┤
│  桌面容器层（Tauri 2）                                    │
│    热键        tauri-plugin-global-shortcut              │
│    系统托盘    tauri-plugin-system-tray                  │
│    通知        tauri-plugin-notification                 │
│    文件对话框  tauri-plugin-dialog                       │
│    文件系统    tauri-plugin-fs                           │
│    Shell 执行  tauri-plugin-shell                        │
│    窗口管理    Tauri 原生多窗口 API                       │
│    HTTP 客户端 tauri-plugin-http（用于 MCP 调用）        │
├──────────────────────────────────────────────────────────┤
│  通信层                                                   │
│    前后端桥接  Tauri Commands (invoke)                    │
│    AI 流式输出 SSE（Server-Sent Events）                  │
│    事件总线    Tauri Events（emit/listen）                │
│    Agent 间通信 内部 FastAPI 路由 + LangGraph 状态机     │
├──────────────────────────────────────────────────────────┤
│  后端引擎层（Python 3.11+）                               │
│    Web 框架    FastAPI + uvicorn                          │
│    Agent 编排  LangGraph 0.2+                            │
│    LLM 抽象    LangChain 0.2+                            │
│    多模型路由  自定义 ModelRouter 类                      │
│    MCP 客户端  mcp（官方 Python SDK）                    │
│    多模态处理  Pillow（图片）、python-docx、PyMuPDF      │
│    音频处理    Librosa + music21（乐谱分析）              │
│    记忆系统    自定义 AgentMemory（SQLite 持久化）        │
├──────────────────────────────────────────────────────────┤
│  执行层                                                   │
│    代码沙盒    subprocess（受限）+ 危险操作白名单拦截     │
│    CLI 工具链  FFmpeg、Pandoc、Marp CLI、Guitar Pro CLI  │
│    文件交付    workspace/exports/ 统一输出目录            │
├──────────────────────────────────────────────────────────┤
│  数据持久层                                               │
│    主数据库    SQLite（aiosqlite 异步驱动）               │
│    Agent 配置  agents_config/ 目录（每 Agent 独立 JSON） │
│    插件注册表  plugins/registry.json                      │
│    工作空间    workspace/（任务文件、交付成果）           │
├──────────────────────────────────────────────────────────┤
│  打包发行层                                               │
│    前端+容器   Tauri build → .exe / .dmg / .AppImage     │
│    Python 后端 PyInstaller → sidecar（随 Tauri 捆绑）   │
└──────────────────────────────────────────────────────────┘
```

### 2.2 关键技术选型理由

| 决策点 | 选择 | 弃用方案 | 弃用原因 |
|--------|------|----------|----------|
| 桌面容器 | Tauri 2 | Electron | Electron 带完整 Chromium，包体 150MB+；Tauri 用系统 WebView，包体 <15MB |
| UI 框架 | React + Vite | PyQt6 + Gradio | Gradio 是数据展示工具，无法实现群聊式 UI 和像素级体验 |
| 状态管理 | Zustand | Redux / MobX | Redux 模板代码是 Zustand 的 5 倍；单人项目优先简洁 |
| Agent 编排 | LangGraph | 手写 task.md 握手 | task.md 无状态追踪、无错误恢复；LangGraph 是专为多 Agent 状态机设计的 |
| MCP 集成 | 官方 Python MCP SDK | 手写协议 | 官方 SDK 维护稳定，兼容所有 MCP Server |
| 音乐分析 | Librosa + music21 | 仅 Librosa | music21 支持五线谱/六线谱导出，与 Guitar Pro 格式对接 |
| 数据库 | SQLite + aiosqlite | JSON 文件 | JSON 文件无事务保护；SQLite 零配置、异步读写 |
| 通信协议 | SSE + Tauri Commands | WebSocket | SSE 单向流更简单；双向操作用 Tauri invoke 更高效 |

---

## 三、目录结构（标准，必须遵守）

```
plobi-agent/
│
├── BLUEPRINT.md                         # 本文件，唯一权威文档
├── package.json                         # 前端根依赖
├── vite.config.ts
├── tsconfig.json
│
├── src-tauri/                           # Tauri / Rust 层
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── capabilities/
│   │   └── default.json                # Tauri 权限声明
│   ├── src/
│   │   ├── main.rs
│   │   ├── commands.rs                  # 所有 Tauri Commands 定义
│   │   ├── tray.rs                      # 系统托盘
│   │   └── sidecar.rs                   # Python sidecar 启动管理
│   └── binaries/                        # PyInstaller 产物放这里
│       └── plobi-backend-{triple}       # 打包时生成
│
├── src/                                 # React 前端
│   ├── main.tsx
│   ├── App.tsx                          # 路由根组件
│   │
│   ├── windows/
│   │   ├── MainWindow.tsx               # 主控台
│   │   └── OverlayWindow.tsx            # 浮窗（Alt+/）
│   │
│   ├── pages/
│   │   ├── Chat.tsx                     # 群聊主页面
│   │   ├── AgentDetail.tsx              # Agent 卡片详情页
│   │   ├── AgentConfig.tsx              # Agent 配置编辑页
│   │   ├── Plugins.tsx                  # 插件管理页
│   │   └── Settings.tsx                 # 全局设置页
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx              # 左侧：会话列表
│   │   │   ├── AgentRail.tsx            # 右侧：Agent 卡片栏（群聊边栏）
│   │   │   ├── ChatPanel.tsx            # 中央：消息流
│   │   │   └── TopBar.tsx
│   │   │
│   │   ├── chat/
│   │   │   ├── MessageBubble.tsx        # 消息气泡（含 Agent 头像）
│   │   │   ├── MessageInput.tsx         # 输入框（含多模态附件）
│   │   │   ├── AttachmentBar.tsx        # 附件预览条
│   │   │   ├── StreamingText.tsx        # 流式打字机渲染
│   │   │   ├── PlanCard.tsx             # plan.md 任务卡片展示
│   │   │   └── TaskProgress.tsx         # 子 Agent 任务进度气泡
│   │   │
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx            # Agent 卡片（头像+名称+状态）
│   │   │   ├── AgentAvatar.tsx          # 头像组件（emoji/图片/文字）
│   │   │   ├── AgentStatusBadge.tsx     # 状态徽章（idle/thinking/running）
│   │   │   └── AgentConfigForm.tsx      # Agent 配置表单
│   │   │
│   │   ├── overlay/
│   │   │   └── OverlayInput.tsx         # 浮窗输入组件
│   │   │
│   │   └── ui/                          # shadcn/ui 自动生成组件
│   │
│   ├── store/
│   │   ├── chatStore.ts                 # 会话 + 消息状态
│   │   ├── agentStore.ts                # Agent 列表 + 状态
│   │   ├── taskStore.ts                 # 任务进度状态
│   │   └── settingsStore.ts             # 全局设置
│   │
│   ├── hooks/
│   │   ├── useStream.ts                 # SSE 流式接收
│   │   ├── useAgentStatus.ts            # Agent 状态轮询
│   │   ├── useFileAttach.ts             # 文件附件处理
│   │   └── useTauri.ts                  # Tauri invoke 封装
│   │
│   ├── lib/
│   │   ├── utils.ts                     # shadcn 工具函数
│   │   ├── fileTypes.ts                 # 文件类型判断
│   │   └── formatters.ts                # 时间、大小格式化
│   │
│   └── styles/
│       ├── globals.css
│       └── glass.css
│
├── backend/                             # Python 后端（独立 Python 项目）
│   ├── main.py                          # FastAPI 入口 + uvicorn
│   ├── requirements.txt
│   │
│   ├── api/
│   │   ├── chat.py                      # /chat/stream SSE
│   │   ├── agents.py                    # /agents CRUD
│   │   ├── tasks.py                     # /tasks 状态查询
│   │   ├── files.py                     # /files 上传处理
│   │   ├── plugins.py                   # /plugins 安装/管理
│   │   └── system.py                    # /system 执行
│   │
│   ├── agents/
│   │   ├── graph.py                     # LangGraph 主状态机
│   │   ├── master.py                    # Master Agent（意图→plan.md→调度）
│   │   ├── researcher.py                # 研究员（新技术/新消息收集）
│   │   ├── engineer.py                  # 工程师（建模软件操控）
│   │   ├── publisher.py                 # 出版官（PPT/论文/课程）
│   │   ├── musician.py                  # 音乐家（音频分析+乐谱）
│   │   ├── videographer.py              # 剪辑师（视频剪辑/生成）
│   │   ├── base_agent.py                # 子 Agent 基类
│   │   └── router.py                    # ModelRouter 多模型路由
│   │
│   ├── memory/
│   │   ├── db.py                        # SQLite 初始化 + 连接池
│   │   ├── session.py                   # 会话 CRUD
│   │   └── agent_memory.py             # Agent 人格记忆 CRUD
│   │
│   ├── planner/
│   │   └── plan_generator.py            # plan.md 生成器
│   │
│   ├── multimodal/
│   │   ├── file_processor.py            # 文件统一处理入口
│   │   ├── image_handler.py             # 图片处理（Pillow）
│   │   ├── audio_handler.py             # 音频处理（Librosa）
│   │   ├── doc_handler.py               # 文档处理（python-docx/PyMuPDF）
│   │   └── music_handler.py             # 乐谱处理（music21）
│   │
│   ├── sandbox/
│   │   └── executor.py                  # 受限代码执行沙盒
│   │
│   ├── mcp/
│   │   ├── client.py                    # MCP Client 管理器
│   │   └── registry.py                  # 已安装 MCP Server 注册表
│   │
│   ├── plugins/
│   │   ├── manager.py                   # 插件安装/卸载/加载
│   │   └── loader.py                    # 动态插件加载器
│   │
│   └── config/
│       ├── models.json                  # 模型配置（.gitignore）
│       └── models.json.example          # 模板（入库）
│
├── agents_config/                       # 每个 Agent 独立配置目录
│   ├── master.json
│   ├── researcher.json
│   ├── engineer.json
│   ├── publisher.json
│   ├── musician.json
│   └── videographer.json
│
├── plugins/                             # 插件目录
│   ├── registry.json                    # 已安装插件注册表
│   └── {plugin-name}/                   # 每个插件一个子目录
│       ├── manifest.json
│       └── main.py
│
└── workspace/                           # Agent 工作目录（运行时）
    ├── plans/                           # plan.md 任务文件
    ├── tasks/                           # 任务中间状态
    └── exports/                         # 所有成果文件交付目录
        ├── documents/
        ├── audio/
        ├── video/
        └── misc/
```

---

## 四、交互架构：双轨 + 群聊式 Agent 面板

### 4.1 主控台布局（群聊式）

```
┌────────────────────────────────────────────────────────────────┐
│  TopBar: [Plobi Logo] [会话名] ········· [插件] [设置] [新建]  │
├──────────────┬─────────────────────────────┬───────────────────┤
│              │                             │                   │
│  Sidebar     │  ChatPanel（群聊消息流）     │  AgentRail        │
│  (220px)     │                             │  (220px)          │
│              │  ┌─────────────────────┐   │                   │
│  会话列表    │  │ 🧠 Master           │   │  ┌─────────────┐  │
│  ──────      │  │ 好的，我来规划...   │   │  │ 🧠 Master   │  │
│  今天        │  └─────────────────────┘   │  │  在线 · 主  │  │
│  · 研究任务  │                             │  └─────────────┘  │
│  · 做PPT     │  ┌─────────────────────┐   │                   │
│  ──────      │  │ 📋 plan.md 卡片     │   │  ┌─────────────┐  │
│  昨天        │  │ ▸ 研究员：收集资料  │   │  │ 🔬 研究员   │  │
│  · 音乐分析  │  │ ▸ 出版官：生成PPT   │   │  │  运行中...  │  │
│              │  └─────────────────────┘   │  └─────────────┘  │
│              │                             │                   │
│              │  ┌─────────────────────┐   │  ┌─────────────┐  │
│              │  │ 🔬 研究员           │   │  │ 📝 出版官   │  │
│              │  │ 我已收集到以下资料: │   │  │  等待中     │  │
│              │  │ [文件: report.md]   │   │  └─────────────┘  │
│              │  └─────────────────────┘   │                   │
│              │                             │  ┌─────────────┐  │
│              │  ─── 输入框 ─────────────  │  │ 🎵 音乐家   │  │
│              │  [📎] [🎤] 发消息给Master  │  │  空闲       │  │
│  [+ 新建]    │  [文本/文件/图片/音频] [↑] │  └─────────────┘  │
└──────────────┴─────────────────────────────┴───────────────────┘
```

**设计要点**：
- 右侧 AgentRail：展示所有 Agent 卡片，点击任意卡片 → 弹出 Agent 详情抽屉（可直接对话）
- 中央 ChatPanel：群聊消息流，每条消息带发送方头像+名称
- plan.md 任务卡片：以可折叠卡片形式内嵌在消息流中，展示任务分解和进度
- 子 Agent 发言：以不同头像气泡出现在消息流中，带状态标识

### 4.2 浮窗（Alt+/）行为

```
唤起：按 Alt+/
  → 屏幕中央弹出药丸型无边框输入框（Liquid Glass 效果）
  → 输入消息，支持粘贴文件路径或拖拽文件

发送（Enter）：
  → 浮窗立即消失
  → 自动打开主控台窗口（若未打开）
  → 自动跳转至 Master Agent 对话
  → 消息发送给 Master Agent，开始流式响应

关闭（Esc）：
  → 浮窗消失，不发送
```

### 4.3 Agent 卡片详情抽屉

点击 AgentRail 中任意 Agent 卡片，在右侧滑出抽屉，内容包括：
- Agent 头像 + 名称 + 当前状态
- 当前任务描述 + 进度条
- 独立对话框（可直接与该 Agent 对话，绕过 Master）
- 任务历史日志（可展开）
- 「配置」按钮 → 跳转到 AgentConfig 页

---

## 五、Master Agent 与子 Agent 分工规范

### 5.1 Master Agent（中枢主控）

**职责**：
1. 与用户直接对话，追问细节，澄清需求
2. 生成标准化 `plan.md` 任务书（见第十一章格式规范）
3. 将任务分发给对应子 Agent
4. 聚合子 Agent 成果，向用户汇报
5. 处理子 Agent 的求助和异常上报

**不做**：
- Master 不直接执行代码
- Master 不直接操作文件系统
- Master 不调用具体工具（交给子 Agent）

**对话风格**（通过 system_prompt 实现）：
- 主动追问关键信息（截止时间？格式要求？受众？）
- 用第一人称，有明确名字和人格
- 汇报时引用子 Agent 名称

### 5.2 子 Agent 分工（6 个默认子 Agent）

| Agent | 标识 | 核心能力 | 优先模型 | 主要工具 |
|-------|------|----------|----------|----------|
| **研究员** Researcher | 🔬 | 新技术/新消息收集、网络检索、信息整理 | DeepSeek / Perplexity | Brave Search MCP、Fetch MCP、firecrawl |
| **工程师** Engineer | ⚙️ | 建模软件操控、代码生成执行、3D/CAD/科学计算 | DeepSeek Coder | Python 沙盒、CLI 工具 |
| **出版官** Publisher | 📝 | PPT/课程/科研论文/技术文档制作 | Claude / GPT-4 | Marp CLI、Pandoc、LaTeX |
| **音乐家** Musician | 🎵 | 音频分析（BPM/和弦/调性）、五线谱/六线谱制作、Guitar Pro 适配 | Claude（音乐理解）| Librosa、music21、Guitar Pro CLI |
| **剪辑师** Videographer | 🎬 | 视频剪辑、字幕生成、视频生成 | 本地/云端视觉模型 | FFmpeg CLI、字幕工具 |
| **侦察兵** Scout | 🛰️ | 实时信息检索、竞品监控（可选，按需启用）| 轻量模型 | MCP 搜索工具 |

**扩展原则**：子 Agent 的数量和分工可通过配置文件扩展，不需要改代码。用户也可以在 UI 里创建自定义子 Agent。

### 5.3 子 Agent 与 Master 的通信

子 Agent 通过 `.md` 文档格式与 Master 交互：
- 接收任务：读取 `workspace/plans/{task_id}_plan.md` 的对应章节
- 汇报成果：写入 `workspace/tasks/{task_id}_{agent_id}_result.md`
- 求助/异常：通过 LangGraph 状态机向 Master 节点发送 `NEED_HELP` 事件

---

## 六、Agent 配置系统

### 6.1 每个 Agent 独立配置文件格式

路径：`agents_config/{agent_id}.json`

```json
{
  "id": "musician",
  "name": "阿奏",
  "avatar": {
    "type": "emoji",
    "value": "🎵"
  },
  "persona": {
    "description": "热爱音乐的 AI 助手，对吉他和乐理有深刻理解",
    "tone": "热情、专业，偶尔用音乐术语",
    "greeting": "嘿！什么风把你吹来了？有什么音乐上的问题？"
  },
  "memory": {
    "enabled": true,
    "user_identity": true,
    "remember_preferences": true,
    "max_memory_items": 50
  },
  "model": {
    "provider": "anthropic",
    "model_id": "claude-opus-4-5",
    "temperature": 0.8,
    "max_tokens": 4096,
    "fallback_provider": "deepseek"
  },
  "skills": [
    "audio_analysis",
    "music_theory",
    "score_generation",
    "guitar_pro_export"
  ],
  "mcp_servers": [
    "filesystem",
    "brave-search"
  ],
  "system_prompt": "你是阿奏，一个精通音乐理论和吉他的 AI 助手...",
  "tools_allowed": [
    "execute_code",
    "read_file",
    "write_file",
    "run_cli"
  ],
  "is_active": true,
  "created_at": "2026-04-25T00:00:00Z"
}
```

**关键设计**：
- 每个 Agent 的 `mcp_servers` 和 `skills` 完全独立，互不干扰
- `model` 独立配置，支持不同 Agent 使用不同模型和参数
- `persona` 字段驱动 system_prompt 中的人格部分
- `memory` 字段控制该 Agent 是否记住用户信息

### 6.2 Agent 人格与记忆实现

```python
# backend/memory/agent_memory.py

class AgentMemory:
    """每个 Agent 独立的记忆空间"""

    def __init__(self, agent_id: str, db):
        self.agent_id = agent_id
        self.db = db

    async def remember(self, key: str, value: str, category: str = "general"):
        """存储一条记忆"""
        await self.db.execute(
            "INSERT OR REPLACE INTO agent_memories VALUES (?,?,?,?,?)",
            (f"{self.agent_id}:{key}", self.agent_id, key, value, category)
        )

    async def recall(self, category: str = None) -> list[dict]:
        """检索记忆"""
        # category 可为: user_identity / preferences / task_history / general
        ...

    async def get_context_injection(self) -> str:
        """生成注入到 system_prompt 的记忆上下文"""
        memories = await self.recall()
        if not memories:
            return ""
        lines = [f"- {m['key']}: {m['value']}" for m in memories]
        return "以下是你记忆中关于用户的信息：\n" + "\n".join(lines)
```

**记忆注入时机**：每次对话前，动态将 `get_context_injection()` 的输出拼接到 system_prompt 末尾。这样 Agent 能记住用户偏好、名字等信息。

### 6.3 Avatar 支持类型

| type | 说明 | value 格式 |
|------|------|------------|
| `emoji` | 单个 emoji | `"🎵"` |
| `text` | 1-2个文字（生成彩色圆形头像）| `"阿奏"` |
| `image` | 本地图片路径 | `"agents_config/avatars/musician.png"` |
| `url` | 远程图片（需联网）| `"https://..."` |

---

## 七、核心模块实现规范

### 7.1 LangGraph 多 Agent 状态机

```python
# backend/agents/graph.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Literal
import operator

class OrchestratorState(TypedDict):
    """全局任务状态，在所有 Agent 节点间传递"""
    session_id: str
    user_message: str
    plan_id: str                               # 当前 plan.md 的 ID
    plan_content: str                          # plan.md 全文
    messages: Annotated[list[dict], operator.add]  # 消息追加语义
    active_agents: list[str]                   # 当前激活的子 Agent 列表
    task_results: dict[str, str]               # {agent_id: result_md}
    status: Literal["planning","dispatching","running","aggregating","done","error"]
    error: str | None

def build_orchestrator() -> StateGraph:
    g = StateGraph(OrchestratorState)

    g.add_node("master_chat", master_chat_node)       # 对话 + 规划
    g.add_node("dispatch", dispatch_node)             # 分发任务到子 Agent
    g.add_node("researcher", researcher_node)
    g.add_node("engineer", engineer_node)
    g.add_node("publisher", publisher_node)
    g.add_node("musician", musician_node)
    g.add_node("videographer", videographer_node)
    g.add_node("aggregate", aggregate_node)           # 聚合所有子 Agent 结果

    g.set_entry_point("master_chat")

    # Master 决定是否需要规划
    g.add_conditional_edges("master_chat", route_after_master, {
        "need_plan": "dispatch",
        "direct_reply": END,
    })

    # 分发后并行启动子 Agent（LangGraph 支持并行节点）
    g.add_conditional_edges("dispatch", route_to_agents, {
        "researcher": "researcher",
        "engineer": "engineer",
        "publisher": "publisher",
        "musician": "musician",
        "videographer": "videographer",
        "aggregate": "aggregate",
    })

    # 所有子 Agent 完成后聚合
    for agent in ["researcher","engineer","publisher","musician","videographer"]:
        g.add_edge(agent, "aggregate")

    g.add_edge("aggregate", END)
    return g.compile()
```

### 7.2 前端：群聊消息流状态结构

```typescript
// store/chatStore.ts

export interface Attachment {
  id: string
  type: 'image' | 'audio' | 'document' | 'video' | 'other'
  name: string
  size: number
  path: string        // 本地临时路径
  mimeType: string
  preview?: string    // base64 缩略图（仅图片）
}

export interface Message {
  id: string
  sessionId: string
  agentId: string           // 发送方 Agent ID（'user' 表示用户）
  role: 'user' | 'assistant' | 'system'
  content: string
  streamBuffer: string      // 流式中临时 buffer
  isStreaming: boolean
  attachments: Attachment[]
  planId?: string           // 若携带 plan.md 卡片
  taskProgress?: {          // 子 Agent 进度信息
    agentId: string
    status: 'pending' | 'running' | 'done' | 'error'
    summary: string
    outputFiles: string[]
  }
  timestamp: number
}

export interface Session {
  id: string
  title: string
  preview: string           // 最后一条消息摘要
  messages: Message[]
  activeAgents: string[]    // 本会话中参与的 Agent ID 列表
  createdAt: number
  updatedAt: number
}
```

### 7.3 前端：流式输出 Hook

```typescript
// hooks/useStream.ts

export function useStream() {
  const { appendToken, setMessageStreaming, addMessage } = useChatStore()

  const startStream = useCallback(async (params: {
    sessionId: string
    agentId: string
    prompt: string
    attachments?: Attachment[]
  }) => {
    const msgId = crypto.randomUUID()

    // 先插入一条空的流式消息占位
    addMessage({
      id: msgId,
      sessionId: params.sessionId,
      agentId: params.agentId,
      role: 'assistant',
      content: '',
      streamBuffer: '',
      isStreaming: true,
      attachments: [],
      timestamp: Date.now(),
    })

    const port = await invoke<number>('get_backend_port')
    const url = new URL(`http://127.0.0.1:${port}/chat/stream`)
    url.searchParams.set('session_id', params.sessionId)
    url.searchParams.set('agent_id', params.agentId)
    url.searchParams.set('message_id', msgId)

    const es = new EventSource(url.toString())

    es.onmessage = (e) => {
      const data: StreamEvent = JSON.parse(e.data)
      switch (data.type) {
        case 'token':
          appendToken(params.sessionId, msgId, data.content)
          break
        case 'agent_status':
          // 子 Agent 状态更新 → 更新 taskStore
          useTaskStore.getState().updateAgentStatus(data.agentId, data.status)
          break
        case 'plan_created':
          // Master 生成了 plan.md → 插入 PlanCard
          addPlanCard(params.sessionId, data.planId, data.planContent)
          break
        case 'file_output':
          // 子 Agent 产出文件 → 在消息中附加文件链接
          appendOutputFile(params.sessionId, msgId, data.filePath)
          break
        case 'done':
          setMessageStreaming(params.sessionId, msgId, false)
          es.close()
          break
        case 'error':
          setMessageStreaming(params.sessionId, msgId, false)
          es.close()
          break
      }
    }

    // 通过 POST 发送消息内容（包含附件引用）
    await fetch(`http://127.0.0.1:${port}/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: params.sessionId,
        agent_id: params.agentId,
        message_id: msgId,
        prompt: params.prompt,
        attachment_ids: params.attachments?.map(a => a.id) ?? [],
      }),
    })
  }, [])

  return { startStream }
}
```

### 7.4 Markdown 渲染（含 plan.md 卡片）

```tsx
// components/chat/MessageBubble.tsx

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeShiki from '@shikijs/rehype'
import 'katex/dist/katex.min.css'

// 代码块组件（带语言标签 + 复制按钮）
function CodeBlock({ language, children }: { language: string; children: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="relative group rounded-lg overflow-hidden border border-border">
      <div className="flex items-center justify-between px-4 py-2 bg-muted text-xs text-muted-foreground">
        <span>{language}</span>
        <button onClick={() => { navigator.clipboard.writeText(children); setCopied(true) }}>
          {copied ? '已复制' : '复制'}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm">{children}</pre>
    </div>
  )
}

export function MessageBubble({ message, agent }: { message: Message; agent?: Agent }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <AgentAvatar agent={isUser ? undefined : agent} isUser={isUser} />
      <div className={`max-w-[70%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {!isUser && (
          <span className="text-xs text-muted-foreground font-medium">
            {agent?.name ?? 'Agent'}
          </span>
        )}
        <div className={`rounded-2xl px-4 py-3 ${isUser
          ? 'bg-accent/15 rounded-tr-sm'
          : 'bg-background border border-border rounded-tl-sm'
        }`}>
          {/* 附件预览 */}
          {message.attachments.length > 0 && (
            <AttachmentBar attachments={message.attachments} />
          )}
          {/* Markdown 内容 */}
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex, [rehypeShiki, { themes: { dark: 'github-dark', light: 'github-light' } }]]}
            components={{
              code: ({ className, children }) => {
                const language = className?.replace('language-', '') ?? 'text'
                return typeof children === 'string' && children.includes('\n')
                  ? <CodeBlock language={language}>{children}</CodeBlock>
                  : <code className="px-1 py-0.5 rounded bg-muted font-mono text-sm">{children}</code>
              }
            }}
          >
            {message.isStreaming
              ? message.streamBuffer + (message.isStreaming ? '▌' : '')
              : message.content}
          </ReactMarkdown>
        </div>
        {/* 任务进度条（子 Agent 消息） */}
        {message.taskProgress && <TaskProgress progress={message.taskProgress} />}
      </div>
    </div>
  )
}
```

### 7.5 Python 后端：FastAPI + SSE 端点

```python
# backend/api/chat.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from agents.graph import build_orchestrator
import json, asyncio

router = APIRouter(prefix="/chat")
orchestrator = build_orchestrator()

@router.get("/stream")
async def stream_chat(session_id: str, agent_id: str, message_id: str):
    """SSE 流式端点：前端先建立 SSE 连接，再 POST /send"""

    async def generate():
        # 等待消息队列（由 /send 推入）
        queue = get_or_create_queue(session_id, message_id)
        try:
            while True:
                event: dict = await asyncio.wait_for(queue.get(), timeout=60)
                yield f"data: {json.dumps(event)}\n\n"
                if event["type"] in ("done", "error"):
                    break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type':'error','message':'timeout'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@router.post("/send")
async def send_message(body: SendMessageRequest):
    """接收用户消息，启动 LangGraph 编排"""
    queue = get_or_create_queue(body.session_id, body.message_id)

    async def run_graph():
        try:
            async for event in orchestrator.astream_events(
                input={
                    "session_id": body.session_id,
                    "user_message": body.prompt,
                    "attachments": body.attachment_ids,
                },
                config={"configurable": {"agent_id": body.agent_id}},
                version="v2"
            ):
                # 将 LangGraph 事件映射为前端事件格式
                await queue.put(map_event(event))
        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})

    asyncio.create_task(run_graph())
    return {"status": "ok"}
```

---

## 八、多模态输入规范

### 8.1 支持的输入类型

| 类型 | 扩展名 | 处理方式 | 传给 LLM 方式 |
|------|--------|----------|----------------|
| **图片** | jpg/png/webp/gif | Pillow 压缩至 ≤2MB | base64 内嵌（Vision API） |
| **PDF** | pdf | PyMuPDF 提取文字+图片 | 文字内容 + 图片分页 |
| **Word** | docx | python-docx 提取 | 纯文字 + 表格 markdown 化 |
| **Markdown** | md/txt | 直接读取 | 原文 |
| **音频** | mp3/wav/flac/m4a | Librosa 分析；transcribe 可选 | 特征 JSON + 转录文字 |
| **视频** | mp4/mov | FFmpeg 提取音频 + 关键帧 | 音频转录 + 关键帧图片 |
| **代码文件** | py/js/ts等 | 读取原文 | 代码块格式 |
| **Guitar Pro** | gp/gpx/gp5 | music21 解析 | 乐谱结构 JSON |

### 8.2 文件处理 Pipeline

```python
# backend/multimodal/file_processor.py

class FileProcessor:
    """统一文件处理入口，根据 MIME 类型路由到专项处理器"""

    async def process(self, file_path: str) -> ProcessedFile:
        mime = detect_mime(file_path)

        if mime.startswith("image/"):
            return await ImageHandler().process(file_path)
        elif mime.startswith("audio/"):
            return await AudioHandler().process(file_path)
        elif mime == "application/pdf":
            return await DocHandler().process_pdf(file_path)
        elif mime in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",):
            return await DocHandler().process_docx(file_path)
        elif file_path.endswith((".gp", ".gpx", ".gp5")):
            return await MusicHandler().process_guitar_pro(file_path)
        else:
            # 文本类文件
            return ProcessedFile(type="text", content=Path(file_path).read_text(errors="replace"))

@dataclass
class ProcessedFile:
    type: str           # text / image / audio / structured
    content: str        # 文字内容或 JSON 结构
    images: list[str]   # base64 图片列表（PDF 分页等）
    metadata: dict      # 额外元信息（时长、BPM、页数等）
```

### 8.3 前端：附件输入组件

```tsx
// components/chat/MessageInput.tsx

export function MessageInput({ sessionId }: { sessionId: string }) {
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [text, setText] = useState('')
  const { startStream } = useStream()
  const { useFileAttach } = useFileAttach()

  const handleFileSelect = async () => {
    // 使用 Tauri 文件对话框
    const selected = await open({
      multiple: true,
      filters: [
        { name: '所有支持格式', extensions: ['jpg','png','pdf','docx','md','txt','mp3','wav','mp4','gp','gpx'] }
      ]
    })
    if (selected) {
      const files = Array.isArray(selected) ? selected : [selected]
      for (const path of files) {
        const attachment = await processAttachment(path)
        setAttachments(prev => [...prev, attachment])
      }
    }
  }

  const handleSend = async () => {
    if (!text.trim() && attachments.length === 0) return
    await startStream({ sessionId, agentId: 'master', prompt: text, attachments })
    setText('')
    setAttachments([])
  }

  return (
    <div className="border-t border-border p-4">
      {/* 附件预览条 */}
      {attachments.length > 0 && <AttachmentBar attachments={attachments} onRemove={...} />}
      <div className="flex items-end gap-2">
        {/* 附件按钮 */}
        <button onClick={handleFileSelect} className="p-2 rounded-lg hover:bg-muted">
          <PaperclipIcon className="w-5 h-5" />
        </button>
        {/* 输入框（支持拖拽文件） */}
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
          onDrop={handleDrop}
          placeholder="发消息给 Master..."
          className="flex-1 resize-none rounded-xl border border-border px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 min-h-[44px] max-h-[200px]"
          rows={1}
        />
        {/* 发送按钮 */}
        <button onClick={handleSend} disabled={!text.trim() && attachments.length === 0}>
          <SendIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
```

---

## 九、MCP 与插件扩展系统

### 9.1 MCP 架构

```
每个 Agent 独立声明其 mcp_servers 列表（见 agents_config/*.json）
    ↓
MCPClientManager 按需启动/复用对应 MCP Server 进程
    ↓
Agent 通过 MCPClient 调用工具（list_tools / call_tool）
    ↓
工具结果注入 LangGraph 状态，继续执行
```

```python
# backend/mcp/client.py

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    """统一管理所有 MCP Server 连接，按需启动，复用连接"""

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._registry = load_registry()  # plugins/registry.json

    async def get_session(self, server_name: str) -> ClientSession:
        if server_name not in self._sessions:
            config = self._registry[server_name]
            params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=config.get("env", {})
            )
            _, session = await stdio_client(params).__aenter__()
            await session.initialize()
            self._sessions[server_name] = session
        return self._sessions[server_name]

    async def call_tool(self, server_name: str, tool_name: str, args: dict) -> str:
        session = await self.get_session(server_name)
        result = await session.call_tool(tool_name, args)
        return result.content[0].text
```

### 9.2 插件安装流程

```python
# backend/plugins/manager.py

class PluginManager:
    """支持用户自主安装插件（MCP Server 或 Python 插件）"""

    REGISTRY_PATH = Path("plugins/registry.json")

    async def install_mcp_server(self, package_name: str) -> dict:
        """安装 NPM 发布的 MCP Server"""
        # 1. npx 方式直接运行（无需全局安装）
        result = await run_cli(f"npm info {package_name} --json")
        info = json.loads(result)

        # 2. 写入注册表
        entry = {
            "name": package_name,
            "type": "mcp_npm",
            "command": "npx",
            "args": ["-y", package_name],
            "description": info.get("description", ""),
            "version": info.get("version", ""),
            "installed_at": datetime.utcnow().isoformat()
        }
        registry = self.load_registry()
        registry[package_name] = entry
        self.save_registry(registry)
        return entry

    async def install_python_plugin(self, plugin_dir: str) -> dict:
        """安装本地 Python 插件（符合插件规范）"""
        manifest_path = Path(plugin_dir) / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        # 验证 manifest 格式...
        # 复制到 plugins/ 目录...
        # 写入注册表...
```

### 9.3 插件 manifest.json 格式

```json
{
  "id": "my-plugin",
  "name": "我的插件",
  "version": "1.0.0",
  "description": "插件描述",
  "type": "python",
  "entry": "main.py",
  "provides": {
    "skills": ["my_skill"],
    "tools": ["my_tool"]
  },
  "requires": {
    "pip": ["requests"]
  },
  "mcp_servers": []
}
```

---

## 十、本地电脑操控规范（CLI 优先 + 沙盒）

### 10.1 操控优先级

```
1. MCP Server（最优先）  →  filesystem MCP、browser MCP 等
2. CLI 命令（优先）      →  ffmpeg、pandoc、marp、guitar-pro 等
3. Python subprocess   →  fallback，需沙盒审批
4. GUI 自动化           →  最后手段，fragile，不主动使用
```

### 10.2 CLI 工具封装规范

每个专业工具封装为独立的 CLI Wrapper：

```python
# backend/sandbox/executor.py

class CLIExecutor:
    """CLI 命令执行器，比 Python 沙盒权限更宽松，但仍有审计日志"""

    ALLOWED_COMMANDS = {
        "ffmpeg": "/usr/bin/ffmpeg",
        "pandoc": "/usr/bin/pandoc",
        "marp": "npx @marp-team/marp-cli",
        "guitar-pro": "C:/Program Files/Guitar Pro 8/GuitarPro.exe",
        "python": sys.executable,
    }

    async def run(self, command: str, args: list[str], cwd: str = None, timeout: int = 120) -> CLIResult:
        # 1. 验证命令是否在白名单
        cmd_name = command.split()[0]
        if cmd_name not in self.ALLOWED_COMMANDS:
            return CLIResult(success=False, error=f"命令 {cmd_name} 不在允许列表中")

        # 2. 记录审计日志
        await self.log_execution(command, args)

        # 3. 执行
        proc = await asyncio.create_subprocess_exec(
            command, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd or str(WORKSPACE)
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return CLIResult(
                success=proc.returncode == 0,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                return_code=proc.returncode
            )
        except asyncio.TimeoutError:
            proc.kill()
            return CLIResult(success=False, error="执行超时")
```

### 10.3 任务成果交付规范

所有子 Agent 的输出文件必须写入 `workspace/exports/{category}/` 目录，并在结果 `.md` 文件中声明产出路径：

```markdown
# 任务结果：音频分析

## 分析摘要
- BPM: 120
- 调性: C Major
- 和弦走向: I-IV-V-I

## 产出文件
- 五线谱: workspace/exports/audio/song_score.mxl
- Guitar Pro: workspace/exports/audio/song.gp
- 分析报告: workspace/exports/documents/song_analysis.pdf
```

---

## 十一、plan.md 任务编排协议

### 11.1 plan.md 格式规范

Master Agent 生成 `workspace/plans/{plan_id}_plan.md`，格式如下：

```markdown
# Plan: {简短任务名}

**Plan ID**: {uuid}
**创建时间**: {ISO 8601}
**状态**: dispatching | running | done | error

## 用户原始需求
{用户原始输入，逐字引用}

## Master 理解
{Master 对需求的解读，澄清了哪些信息}

## 任务分解

### 任务 1 — 研究员
**负责 Agent**: researcher
**任务描述**: 收集关于 {topic} 的最新资料，整理成结构化报告
**输入**: 用户提供的关键词、时间范围限制
**预期产出**: `workspace/tasks/{plan_id}_researcher_result.md`
**依赖**: 无
**状态**: pending

### 任务 2 — 出版官
**负责 Agent**: publisher
**任务描述**: 基于研究员的报告，生成 20 页 PPT
**输入**: 任务 1 的产出
**预期产出**: `workspace/exports/documents/{plan_id}_presentation.pptx`
**依赖**: 任务 1
**状态**: waiting

## 时间预估
- 任务 1: ~3 分钟
- 任务 2: ~2 分钟（依赖任务 1）
- 总计: ~5 分钟
```

### 11.2 plan.md 前端展示（PlanCard）

plan.md 在前端以可交互卡片形式展示：
- 可折叠/展开任务列表
- 每个任务项有状态指示器（等待/运行中/完成/错误）
- 点击任务项 → 跳转到对应子 Agent 的详情
- 完成后高亮展示产出文件链接（可点击在系统文件管理器打开）

---

## 十二、数据库 Schema（SQLite）

```sql
-- 会话表
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  preview TEXT DEFAULT '',
  primary_agent_id TEXT NOT NULL DEFAULT 'master',
  active_agent_ids TEXT NOT NULL DEFAULT '[]',  -- JSON 数组
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- 消息表（含多模态附件）
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  agent_id TEXT NOT NULL,                   -- 发送方 Agent ID
  role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
  content TEXT NOT NULL,
  attachments TEXT DEFAULT '[]',            -- JSON 数组，每项含 {id,type,name,path}
  plan_id TEXT,                             -- 关联 plan.md 的 ID
  metadata TEXT DEFAULT '{}',              -- JSON，扩展字段
  created_at INTEGER NOT NULL
);
CREATE INDEX idx_messages_session ON messages(session_id, created_at);

-- Agent 配置表（从 agents_config/*.json 同步，作为运行时查询缓存）
CREATE TABLE agents (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  avatar_json TEXT NOT NULL,
  persona_json TEXT NOT NULL,
  model_json TEXT NOT NULL,
  skills TEXT DEFAULT '[]',
  mcp_servers TEXT DEFAULT '[]',
  system_prompt TEXT NOT NULL,
  is_active INTEGER DEFAULT 1,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- Agent 记忆表（每个 Agent 独立记忆空间）
CREATE TABLE agent_memories (
  id TEXT PRIMARY KEY,          -- "{agent_id}:{key}"
  agent_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  category TEXT DEFAULT 'general',  -- user_identity / preferences / task_history / general
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX idx_memories_agent ON agent_memories(agent_id, category);

-- 任务表（plan.md 对应的结构化任务）
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  session_id TEXT REFERENCES sessions(id),
  agent_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT CHECK(status IN ('pending','waiting','running','done','error')) DEFAULT 'pending',
  input_refs TEXT DEFAULT '[]',      -- JSON：依赖的其他任务 ID 或文件路径
  output_files TEXT DEFAULT '[]',    -- JSON：产出文件路径列表
  error TEXT,
  created_at INTEGER NOT NULL,
  started_at INTEGER,
  completed_at INTEGER
);

-- 执行审计日志（CLI + 代码执行记录）
CREATE TABLE execution_logs (
  id TEXT PRIMARY KEY,
  task_id TEXT REFERENCES tasks(id),
  agent_id TEXT NOT NULL,
  type TEXT CHECK(type IN ('cli','python','mcp')),
  command TEXT NOT NULL,
  args TEXT DEFAULT '[]',
  status TEXT CHECK(status IN ('pending','running','done','error','blocked')),
  stdout TEXT,
  stderr TEXT,
  created_at INTEGER NOT NULL,
  completed_at INTEGER
);

-- 插件注册表（运行时缓存，源文件是 plugins/registry.json）
CREATE TABLE plugins (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT,
  type TEXT CHECK(type IN ('mcp_npm','mcp_local','python')),
  manifest_json TEXT NOT NULL,
  is_enabled INTEGER DEFAULT 1,
  installed_at INTEGER NOT NULL
);
```

---

## 十三、API 接口规范

所有后端接口监听 `http://127.0.0.1:52731`，仅本地访问。**云端部署时此端口改为 JWT 鉴权的公网端口（见第十五章预留设计）。**

### 聊天 & 流式
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/chat/stream?session_id=&agent_id=&message_id=` | SSE 流式输出 |
| POST | `/chat/send` | 发送消息（触发 LangGraph）|

### 会话管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sessions` | 获取所有会话 |
| POST | `/sessions` | 新建会话 |
| GET | `/sessions/{id}` | 获取会话详情 |
| DELETE | `/sessions/{id}` | 删除会话 |
| GET | `/sessions/{id}/messages` | 获取消息历史 |

### Agent 管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/agents` | 获取 Agent 列表 |
| GET | `/agents/{id}` | 获取 Agent 详情 |
| PUT | `/agents/{id}` | 更新 Agent 配置 |
| POST | `/agents` | 新建自定义 Agent |
| DELETE | `/agents/{id}` | 删除 Agent |
| GET | `/agents/{id}/memories` | 获取 Agent 记忆 |
| DELETE | `/agents/{id}/memories` | 清空 Agent 记忆 |

### 任务 & 文件
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tasks/{plan_id}` | 获取 plan 下所有任务状态 |
| POST | `/files/upload` | 上传附件（multipart）|
| GET | `/files/{id}` | 获取文件信息 |
| GET | `/workspace/exports` | 列出所有产出文件 |

### 插件
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plugins` | 获取已安装插件列表 |
| POST | `/plugins/install/npm` | 安装 NPM MCP Server |
| POST | `/plugins/install/local` | 安装本地插件 |
| DELETE | `/plugins/{id}` | 卸载插件 |
| PUT | `/plugins/{id}/toggle` | 启用/禁用插件 |

---

## 十四、Token 消耗优化策略

**原则**：在保证体验的前提下尽量少消耗 Token。

### 14.1 架构层面

1. **Master 不重复执行**：Master 只做规划和汇报，不自己执行任务，避免大模型调用昂贵工具
2. **子 Agent 用小模型**：对话智能的 Master 用大模型（Claude），执行型子 Agent（工程师、剪辑师）用 DeepSeek Coder 或本地 Ollama
3. **文件中转减少上下文**：子 Agent 之间通过文件传递大体积内容，而不是把全文塞进消息上下文
4. **滑动窗口记忆**：每个会话保留最近 20 条消息作为上下文，更早的消息自动摘要压缩

### 14.2 实现层面

```python
# backend/memory/session.py — 滑动窗口实现

CONTEXT_WINDOW_SIZE = 20      # 最近 N 条消息全文保留
SUMMARY_TRIGGER = 40          # 超过此数量触发摘要

async def get_context_messages(session_id: str) -> list[dict]:
    all_messages = await db.fetchall(
        "SELECT * FROM messages WHERE session_id=? ORDER BY created_at",
        (session_id,)
    )
    if len(all_messages) <= CONTEXT_WINDOW_SIZE:
        return all_messages

    # 超出窗口的消息用摘要替代
    older = all_messages[:-CONTEXT_WINDOW_SIZE]
    recent = all_messages[-CONTEXT_WINDOW_SIZE:]

    summary = await get_or_create_summary(session_id, older)
    return [{"role": "system", "content": f"[早期对话摘要]: {summary}"}] + recent
```

### 14.3 前端层面

- 消息列表使用 `@tanstack/react-virtual` 虚拟滚动，避免渲染几千条消息
- 大文件只传路径引用给后端，不在前端存储内容
- 附件预览图限制在 200px，不加载原图

---

## 十五、云端部署预留设计

当前是纯本地桌面应用。以下设计确保未来可以平滑迁移到云端，**现在只做架构预留，不实现**。

### 15.1 关键隔离点

| 当前（本地）| 云端迁移后 |
|-------------|------------|
| FastAPI 监听 `127.0.0.1:52731` | FastAPI 监听 `0.0.0.0:8000` + HTTPS + JWT |
| SQLite 文件数据库 | PostgreSQL（SQLAlchemy 切换） |
| 本地文件系统（workspace/）| 对象存储（S3/MinIO）|
| Tauri Sidecar 拉起后端 | Docker/K8s 部署后端 |
| 无鉴权 | JWT + OAuth2 |

### 15.2 配置抽象层（现在就做）

```python
# backend/config/settings.py — 统一配置读取，方便未来切换

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./plobi.db"
    # 文件存储
    STORAGE_BACKEND: str = "local"             # local | s3
    STORAGE_LOCAL_PATH: str = "./workspace"
    STORAGE_S3_BUCKET: str = ""
    # 鉴权（本地模式留空）
    AUTH_ENABLED: bool = False
    JWT_SECRET: str = ""
    # 后端地址（前端读取）
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 52731

    class Config:
        env_file = ".env"

settings = Settings()
```

前端读取后端地址也走统一配置：
```typescript
// src/lib/config.ts
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:52731'
```

---

## 十六、UI/UX 设计规范

### 16.1 颜色系统（CSS 变量，亮暗双模式）

```css
/* src/styles/globals.css */
:root {
  --accent:        #0084FF;
  --accent-hover:  #0070DB;
  --accent-muted:  rgba(0,132,255,0.12);

  --bg-0:   #FFFFFF;                   /* 最底层背景 */
  --bg-1:   #F7F7F5;                   /* 侧边栏 */
  --bg-2:   #EFEFED;                   /* 悬浮卡片、输入框 */
  --bg-3:   rgba(255,255,255,0.65);    /* Glass 层 */

  --text-primary:   #1A1A1A;
  --text-secondary: #6B6B6B;
  --text-muted:     #9A9A9A;

  --border:        rgba(0,0,0,0.08);
  --border-strong: rgba(0,0,0,0.15);

  --success: #22C55E;
  --warning: #F59E0B;
  --error:   #EF4444;
  --running: #3B82F6;
}

[data-theme="dark"] {
  --bg-0:   #1A1A1A;
  --bg-1:   #222222;
  --bg-2:   #2A2A2A;
  --bg-3:   rgba(30,30,30,0.75);
  --text-primary:   #F0F0EE;
  --text-secondary: #9A9A9A;
  --text-muted:     #666666;
  --border:        rgba(255,255,255,0.08);
  --border-strong: rgba(255,255,255,0.15);
}
```

### 16.2 Agent 状态颜色语义

| 状态 | 颜色 | 含义 |
|------|------|------|
| idle（空闲）| `--text-muted` | 无任务 |
| thinking（思考）| `--running` + 脉冲动画 | 正在生成回复 |
| running（执行）| `--warning` + 旋转图标 | 正在执行 CLI/代码 |
| done（完成）| `--success` | 本次任务完成 |
| error（错误）| `--error` | 需要用户介入 |

### 16.3 Liquid Glass（仅浮窗和抽屉）

```css
.glass {
  backdrop-filter: blur(40px) saturate(1.8);
  -webkit-backdrop-filter: blur(40px) saturate(1.8);
  background: var(--bg-3);
  border: 1px solid var(--border);
  box-shadow: inset 0 1px 1px rgba(255,255,255,0.25), 0 8px 32px rgba(0,0,0,0.1);
}
.overlay-pill { border-radius: 32px; height: 56px; padding: 0 20px; }
```

### 16.4 组件设计规则

- 侧边栏会话项：高 44px，选中左侧 2px accent 色 border
- AgentRail 卡片：宽 200px，含头像+名称+状态徽章，点击展开抽屉
- 消息气泡：用户消息右对齐+accent-muted 背景；Agent 消息左对齐+无背景（仅 border）
- plan.md 卡片：折叠默认展示，任务状态实时更新
- 流式光标：`▌` 字符，1s 闪烁，流式结束后消失
- 代码块：暗色背景 `#1e1e1e`（不跟随主题），右上角语言标签+复制按钮

---

## 十七、打包发行规范

### 17.1 Python Sidecar 打包

```bash
cd backend
pip install pyinstaller
pyinstaller --onefile --noconsole \
  --add-data "config;config" \
  --add-data "plugins;plugins" \
  --hidden-import music21 \
  --hidden-import librosa \
  --name plobi-backend \
  main.py

# Windows
cp dist/plobi-backend.exe ../src-tauri/binaries/plobi-backend-x86_64-pc-windows-msvc.exe
# macOS (arm)
cp dist/plobi-backend ../src-tauri/binaries/plobi-backend-aarch64-apple-darwin
```

### 17.2 Tauri 打包

```bash
# 开发调试
npm run tauri dev

# 生产构建
npm run tauri build
# 输出: src-tauri/target/release/bundle/
#   Windows: plobi-agent_1.0.0_x64-setup.exe
#   macOS: plobi-agent_1.0.0_aarch64.dmg
```

### 17.3 tauri.conf.json 关键配置

```json
{
  "productName": "Plobi Agent",
  "version": "1.0.0",
  "bundle": {
    "externalBin": ["binaries/plobi-backend"],
    "icon": ["icons/32x32.png","icons/128x128.png","icons/icon.icns","icons/icon.ico"]
  },
  "app": {
    "windows": [
      {
        "label": "main",
        "title": "Plobi Agent",
        "width": 1280, "height": 800,
        "minWidth": 960, "minHeight": 600,
        "visible": false, "center": true
      },
      {
        "label": "overlay",
        "width": 640, "height": 72,
        "decorations": false, "transparent": true,
        "alwaysOnTop": true, "skipTaskbar": true,
        "visible": false, "center": true,
        "url": "overlay.html"
      }
    ]
  }
}
```

---

## 十八、开发里程碑

### Phase 1：端到端最小闭环（当前）
**目标**：按 `Alt+/` 发问 → 主控台 Master Agent 流式回复

- [ ] `create-tauri-app` 初始化（React + TypeScript）
- [ ] Tailwind CSS + shadcn/ui 配置
- [ ] 双窗口（main + overlay）
- [ ] `Alt+/` 热键 → 浮窗 → 发送后跳主控台 Master
- [ ] FastAPI 后端 + `/chat/stream` SSE（直连 DeepSeek，跳过 LangGraph）
- [ ] `useStream` Hook + Zustand + 流式渲染
- [ ] 系统托盘
- [ ] SQLite 初始化 + 基础会话 CRUD

**交付标准**：端到端流式对话跑通，浮窗跳转正常。

---

### Phase 2：群聊 UI + 基础 Agent 面板
**目标**：达到群聊式多 Agent 视觉效果

- [ ] Sidebar 会话列表（分组：今天/昨天/更早）
- [ ] AgentRail（右侧 Agent 卡片栏）
- [ ] AgentCard + AgentStatusBadge
- [ ] Agent 详情抽屉（点击卡片展开）
- [ ] MessageBubble 带 Agent 头像 + 名称
- [ ] 完整 Markdown 渲染（GFM + 代码高亮 + 数学公式）
- [ ] 多模态附件输入（图片+文档+音频）
- [ ] 亮/暗主题切换

**交付标准**：UI 达到群聊体验，可发送带附件的消息。

---

### Phase 3：LangGraph 多 Agent 编排
**目标**：Master → plan.md → 子 Agent 任务流真正跑通

- [ ] LangGraph 状态机完整实现
- [ ] Master Agent system_prompt + 追问逻辑
- [ ] plan.md 生成器 + 前端 PlanCard 展示
- [ ] 研究员 Agent（Brave Search MCP）
- [ ] 出版官 Agent（Marp CLI → PPT）
- [ ] 任务进度实时推送到前端
- [ ] 产出文件链接（点击在文件管理器打开）

**交付标准**：输入「帮我做一个关于 AI 的 PPT」→ Master 追问→生成 plan.md → 研究员收集 → 出版官生成 PPT → 文件链接出现在消息中。

---

### Phase 4：Agent 配置 + 人格记忆 + 插件
**目标**：Agent 深度自定义

- [ ] AgentConfigForm（头像/名称/模型/Skill 配置）
- [ ] Agent 记忆系统（AgentMemory CRUD）
- [ ] 记忆注入到 system_prompt
- [ ] 插件管理 UI（列表 + 安装 + 启用/禁用）
- [ ] MCP 安装（npm 方式）
- [ ] 音乐家 Agent（Librosa + music21 + Guitar Pro）
- [ ] 工程师 Agent（代码执行 + 沙盒确认弹窗）
- [ ] 剪辑师 Agent（FFmpeg CLI）

**交付标准**：可在 UI 新建自定义 Agent，安装 MCP 插件，Agent 记住用户名字。

---

### Phase 5：打包发行 + 云端预留
**目标**：单文件安装包 + 云端迁移能力

- [ ] PyInstaller sidecar 编译测试
- [ ] Tauri build 全平台测试（Windows + macOS）
- [ ] 首次启动引导（API Key 配置向导）
- [ ] 自动更新（tauri-plugin-updater）
- [ ] settings.py 云端配置切换测试（PostgreSQL + S3）
- [ ] JWT 鉴权层预留接口

---

## 十九、工程纪律（AI 工具必读）

**本项目 AI 编程助手在每次会话开始时必须先读取本文件，然后严格遵守以下规则：**

1. **技术栈锁定**：不得引入本文件技术栈以外的框架库。如确有必要，必须先在本文件「技术栈决策」章节注明理由并更新。

2. **组件命名强制规范**：
   - React 组件文件：`PascalCase.tsx`
   - Hook 文件：`camelCase.ts`，必须以 `use` 开头
   - Store 文件：`camelCase.ts`，必须以 `Store` 结尾
   - Python 模块：`snake_case.py`

3. **禁止 `any` 类型**：TypeScript 代码必须有明确类型声明。接口/类型改动必须同步更新对应 `interface`/`type`。

4. **SSE 是唯一 AI 流式通道**：不得用 WebSocket 替代 SSE 传输 AI token。

5. **所有数据库操作走 memory/ 层**：不得在 `api/` 层直接写 SQL，所有 DB 操作封装在 `backend/memory/` 的 async 函数中。

6. **沙盒 require_confirm=True 是默认值**：调用 `SandboxExecutor.execute()` 或 `CLIExecutor.run()` 时，涉及写文件/系统修改的操作，必须先获取前端用户确认。

7. **配置文件不入库**：`backend/config/models.json` 永远在 `.gitignore` 中，只有 `models.json.example` 入库。

8. **Agent 配置独立存储**：每个 Agent 的配置文件 `agents_config/{id}.json` 独立存在，不合并到单一配置文件。

9. **文件产出只写 workspace/exports/**：子 Agent 的所有产出文件必须写入此目录的对应子目录，不得随意写入用户文件系统其他位置（除非用户明确指定目标路径）。

10. **每个 Phase 完成后更新本文档**：勾选已完成的里程碑项，并在对应 Phase 下方补充实际实现中的变更和踩坑记录。

---
*如有架构变更，以本文件最新版本为准，所有开发会话以本文件为起点。*
那你按原计划继续往后推进，要求如下
1、严格按照BLUEPRINT.md执行
2、一次性不要推进太多，但一定要高质量完成，宁愿慢一点或或按多一点token
3、遇到设计上的问题及时问我
4、推进到用户可测试点，让我测试一下。验收合格后再继续
5、完成后记得及时更新task.md
6、我是小白，测试的时候你要告诉我具体的测试步骤