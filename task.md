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

### 待完成项
- [ ] SQLite 初始化 + 会话 CRUD (Phase 2)
- [ ] LangGraph 集成 (Phase 2)
- [ ] 文件上传/处理 (Phase 2)
- [ ] MCP 插件系统 (Phase 3)

## Phase 2 - 核心功能 (待开始)
- [ ] SQLite 数据库初始化
- [ ] 会话持久化 (CRUD)
- [ ] LangGraph Master Agent 实现
- [ ] 子 Agent 调度 (研究员、工程师、出版官等)
- [ ] 文件上传与处理 (图片、PDF、音频、视频)
- [ ] task.md 文件监控与执行协议

## Phase 3 - 插件与扩展 (待开始)
- [ ] MCP 客户端管理器
- [ ] 插件安装系统 (NPM + Python)
- [ ] CLI 工具封装
- [ ] 任务输出到 workspace/exports/

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

# 启动前端开发服务器
npm run dev

# 构建 Tauri 应用
npm run tauri build
```
