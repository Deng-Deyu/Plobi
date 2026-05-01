
# Plobi Agent 开发任务

## Phase 1 - 脚手架搭建 ✅ 已完成

### 已完成项
- [x] 删除旧框架文件 (Gradio, PyQt6, core/, config/, sessions/, static/, views/, avatars/, scripts/, tests/, design/)
- [x] 安装 Rust 工具链
- [x] 创建 Tauri + React 项目骨架
  - package.json, vite.config.ts, tsconfig.json, tsconfig.node.json
  - index.html, overlay.html
  - src-tauri/Cargo.toml, build.rs, tauri.conf.json
  - src-tauri/src/main.rs, commands.rs, tray.rs
- [x] 配置 Tailwind CSS + PostCSS
  - tailwind.config.js, postcss.config.js
  - src/styles/globals.css, src/styles/glass.css
- [x] 创建 FastAPI 后端 + SSE /chat/stream
  - backend/main.py (FastAPI + SSE 直连 DeepSeek)
  - backend/requirements.txt
- [x] 实现 Zustand stores + useStream Hook
  - src/store/chatStore.ts, agentStore.ts, taskStore.ts, settingsStore.ts
  - src/hooks/useStream.ts, useTauri.ts
  - src/lib/formatters.ts
- [x] 创建 React 组件
  - src/components/layout/TopBar.tsx, Sidebar.tsx, AgentRail.tsx, ChatPanel.tsx
  - src/components/chat/MessageBubble.tsx, MessageInput.tsx
  - src/components/agents/AgentCard.tsx, AgentAvatar.tsx, AgentStatusBadge.tsx
  - src/components/overlay/OverlayInput.tsx
- [x] 双窗口 + Alt+/ 热键 + 系统托盘
  - tauri.conf.json 配置 main 和 overlay 窗口
  - global-shortcut Alt+/ 切换 overlay
  - tray.rs 系统托盘菜单
- [x] 运行 npm install 安装依赖
- [x] 创建目录结构
  - agents_config/, workspace/, plugins/, workspace/exports/

## Phase 2 - 核心功能 ✅ 已完成
- [x] SQLite 数据库初始化
- [x] 会话持久化 (CRUD)
- [x] LangGraph Master Agent 实现
- [x] 子 Agent 调度 (研究员、工程师、出版官等)
- [x] 文件上传与处理 (图片、PDF、音频、视频)

## Phase 3 - 插件与扩展 ✅ 已完成
- [x] MCP 客户端管理器
- [x] 插件安装系统 (NPM + Python)
- [x] CLI 工具封装
- [x] 任务输出到 workspace/exports/

## Phase 4 - Agent 配置与插件 ✅ 已完成
- [x] Agent 配置 API (backend/api/agents.py)
- [x] Agent 配置界面 (AgentConfigForm)
- [x] Agent 记忆系统 (CRUD + 注入 system_prompt + 前端管理)
- [x] 插件管理 UI (列表 + 启用/禁用 + 安装/卸载)
- [x] 工程师 Agent - 代码执行沙盒 (backend/api/sandbox.py + SandboxConfirm 弹窗)
- [x] 剪辑师 Agent - FFmpeg CLI (system_prompt + SANDBOX 标记)
- [x] 音乐家 Agent - Librosa + music21 (system_prompt + SANDBOX 标记)

## 已知问题
- [ ] Overlay 窗口输入消息后按回车无法跳转至主窗口对话 (Tauri 跨窗口事件通信待调试)
- [ ] 系统托盘最小化后恢复窗口待验证

## 环境配置
- Node.js: 已安装
- Rust: 已安装
- Python: 3.11+
- 后端端口: 52731
- DeepSeek API: 需在 .env 中配置 DEEPSEEK_API_KEY

## 启动命令
```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 启动后端
python main.py

# 启动 Tauri 应用 (包含前端)
npm run tauri dev

# 构建生产版本
npm run tauri build
```
