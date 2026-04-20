# AI OS V4.0 - 统一液态玻璃智能系统开发计划

## 1. 项目定位与核心场景

* **定位**：纯本地化、高度自定义的个人桌面级多智能体自动化总控平台。
* **核心特性**：拒绝黑盒执行、极简 Token 消耗（文件级异步中转）、Liquid Glass 拟态 UI、无边框沉浸式交互、SPA 单页应用架构、实时主题切换。
* **核心场景**：
  * **系统级自动化**：读取自然语言指令，本地执行 Python/Shell 脚本处理文件与环境。
  * **学术与文档渲染**：文献检索数据结构化，Markdown 极速转制高颜值 PPT 与排版论文。
  * **音频分析流水线**：音乐轨道的 BPM 侦测、和弦走向提取与吉他指弹前置参数分析。

## 2. 详细功能清单

| 模块 | 功能项 | 详细描述 |
| :--- | :--- | :--- |
| **交互入口** | 悬浮唤醒 | `Alt+/` 全局热键唤出，系统托盘驻留，无边框拖拽。 |
| | Search-to-Chat | 主页极简多模态搜索框，回车自动路由跳转至对应工作区。 |
| **智能体矩阵** | 助理 (Master) | 中枢节点。解析意图，生成标准化 `.md` 任务书，不直接执行代码。 |
| | 极客 (Sub) | 自动化专家。读取任务书，调度 Open Interpreter 执行底层操作。 |
| | 出版官 (Sub) | 文理双修引擎。执行 Pandoc/Marp 文档编译与 Librosa 音频特征提取。 |
| | 构筑师/侦察兵 (Sub) | 软件脚手架搭建与基于 MCP 协议的外网情报抓取。 |
| **记忆引擎** | 会话持久化 | Session Manager 实时将会话存入本地 JSON，支持侧边栏动态加载与切换。 |
| **UI/UX** | Liquid Glass 特效 | 毛玻璃模糊、内阴影、高光效果，现代化卡片设计。 |
| | SPA 路由 | 单页应用导航，支持面板间无缝切换（Home、Model、Agents、Settings）。 |
| | 主题切换 | 实时 Light/Dark 模式切换，基于 CSS 变量与 JavaScript 事件绑定。 |
| **配置管理** | 模型配置 | 支持 DeepSeek、Ollama、OpenAI、Claude 多引擎，API 密钥安全存储。 |
| | Agent 配置 | 5 个 Agent（助理、极客、构筑师、出版官、侦察兵）独立系统提示词。 |
| | 自动保存 | 输入框变化时自动保存配置，gr.Info 通知用户。 |

## 3. 系统分层架构图（文字描述）

系统采用 **Master-Sub 主从架构** 与 **四层解耦设计**：

* **[表示层 / Presentation Layer]**
  * 宿主容器：PyQt6（管控窗口生命周期、托盘、系统级热键）。
  * 渲染内核：Gradio 6.0 + 自定义 HTML/CSS（负责 Liquid Glass 特效与 SPA 路由）。
  * SPA 路由引擎：基于 `switch_panel()` 函数实现面板切换，支持卡片点击与导航栏路由。
* **[路由控制层 / Routing Layer]**
  * 状态机与 SPA 拦截器（控制主页 -> 助理面板 -> 专家卡片的可见性切换）。
  * Session I/O 控制器。
  * 主题管理器：通过 JavaScript 绑定 CSS 变量，实时切换 Light/Dark 模式。
* **[认知中枢层 / Cognitive Layer]**
  * LLM 引擎切换器（支持云端 DeepSeek API 与本地离线 Ollama）。
  * 模型配置管理器：从 `config/models_config.json` 加载配置，支持自动保存。
* **[物理执行层 / Execution Layer]**
  * 沙盒化执行器：Open Interpreter。
  * 专业算力单元：FFmpeg, Librosa, Pandoc。
  * 上下文桥梁：MCP (Model Context Protocol)。

## 4. 核心模块设计

* **Markdown 异步握手协议**：彻底斩断 Agent API 之间的直接调用。Assistant 生成需求写入 `/Workspace/task.md`，执行类 Agent 启动时仅挂载该文件作为 System Prompt 上下文。大幅降低 Token 消耗并消除无限死循环风险。
* **双轨音频与排版引擎**：
  * *排版轨*：劫持 LLM 输出流中的特定分隔符（如 `---`），管道传输至 `Marp-CLI` 瞬间生成 PDF/PPT。
  * *音频轨*：挂载 `librosa.beat` 与 `chroma_cqt` 算法，在服务端预处理 22050Hz 采样率音频，输出结构化 JSON 数据给 LLM 辅助谱面编配。
* **SPA 路由系统**：
  * 通过 `switch_panel()` 函数统一管理所有面板可见性。
  * 主页卡片点击触发面板切换，导航栏提供全局导航。
  * 基于 Gradio 的 `.update(visible=True/False)` 实现无刷新切换。
* **主题切换系统**：
  * CSS 变量定义 Light/Dark 颜色方案。
  * JavaScript 事件监听 Radio 组件变化，实时更新 `document.documentElement.style.setProperty`。
  * 即时视觉反馈，无需页面重载。

## 5. 最终技术选型+对比理由

| 选型领域 | 最终方案 | 竞品对比与弃用理由 |
| :--- | :--- | :--- |
| **桌面框架** | **PyQt6 + Gradio** | 弃用 Electron：内存开销极大，且前后端双语开发增加维护成本。PyQt6 提供系统级权限，Gradio 确保 Python 全栈极速迭代。 |
| **大模型基座** | **DeepSeek API + Ollama** | 弃用单 OpenAI 方案：DeepSeek 提供极致代码生成性价比；Ollama 保障纯本地断网时的隐私安全。 |
| **自动化引擎** | **Open Interpreter** | 弃用 PyAutoGUI：基于坐标的模拟点击极其脆弱。直接赋予 LLM 生成并运行 Python/Shell 脚本的能力，鲁棒性具备降维打击优势。 |
| **UI 架构** | **SPA + Liquid Glass CSS** | 弃用多页面应用：SPA 提供无缝用户体验，CSS 变量实现动态主题，backdrop-filter 实现毛玻璃效果。 |

## 6. 关键技术难点与解决方案

* **难点 1：Gradio Web UI 在桌面定尺寸窗口的比例失调**
  * *方案*：通过 `gr.HTML` 注入 `:root` CSS 变量，强行覆盖 `--size-4`, `--text-lg` 等基准值，实现全局组件的等比极限压缩，完美适配 1000x700 窗口。
* **难点 2：SPA 架构下的组件事件脱落**
  * *方案*：严禁使用纯 HTML 标签绑定路由。通过高度自定义 CSS 强行剥离原生 `gr.Button` 的样式（背景透传、消灭灰色边框），使其伪装成卡片，从而保留 Gradio 原生的 `.click()` 事件循环能力。
* **难点 3：实时主题切换与 CSS 变量动态更新**
  * *方案*：通过 JavaScript 监听 Radio 组件变化，动态更新 CSS 变量，避免页面重载。定义完整的 Light/Dark 颜色方案变量。

## 7. 安全与权限控制

* **执行拦截机制**：Open Interpreter 配置为显式确认模式（`auto_run=False`），在执行涉及 `os.remove`、`rm -rf` 等敏感系统命令前，必须通过 Gradio 界面拦截并等待用户同意。
* **系统隔离**：所有的自动化文件操作被强行圈定在预设的 `/Workspace` 沙盒目录下，跨目录读写需提权审批。
* **配置安全**：API 密钥存储在本地 JSON 配置文件中，通过 `.gitignore` 排除，避免意外提交。

## 8. 开发里程碑（已完成 → 未来规划）

* **Phase 1：视觉与宿主基建** → 跑通 PyQt6 悬浮、Liquid Glass UI、Gradio 路由。（已完成）
* **Phase 2：记忆与主从流转** → 接入 DeepSeek、完成 Search-to-Chat 跳转、落地 Session Manager 本地存取。（已完成）
* **Phase 3：物理能力注入** → 集成 Marp/Pandoc 学术排版能力；集成 Librosa 指弹音频分析流水线。（规划中）
* **Phase 4：全域接管与 RAG** → 接入 Zotero 本地文献库进行 RAG 检索；GUI 层实现代码崩溃日志拦截与接管。（规划中）
* **Phase 5：SPA 路由与导航** → 实现单页应用架构，卡片点击切换面板，统一导航栏。（已完成）
* **Phase 6：主题切换系统** → 实现 Light/Dark 模式实时切换，CSS 变量动态更新。（已完成）
* **Phase 7：工程清理与核心功能布线** → 标准化 .gitignore，重命名入口为 `main.py`，删除废弃文件，连接聊天逻辑与模型配置自动保存。（已完成）

## 9. 部署打包方案

* **工具**：`PyInstaller`。
* **编译策略**：使用 `--noconsole` 与 `--windowed` 隐藏终端黑框。
* **静态资源剥离**：将 Gradio 的前端静态文件、配置文件 (`models_config.json`, `agents_config.json`) 及自定义 CSS 通过 `--add-data` 显式打包。
* **模型解耦**：桌面程序本体应控制在 200MB 以内，Ollama 及大模型由用户在首次启动后引导异步拉取，防止安装包体积臃肿。

## 10. 风险与优化方向

* **风险：Python 科学计算包导致的依赖膨胀**。引入 `Librosa` 和 `SciPy` 会导致打包体积急剧增加。
  * *优化*：在 PyInstaller 的 `.spec` 文件中，严格配置 `excludes`，剔除 matplotlib, PyQtWebEngine 等不必要的庞大依赖。
* **风险：长下文导致的 Token 溢出与响应延迟**。
  * *优化*：在 Session Manager 加载历史记录时，实现滑动窗口截断（仅保留最近 10 轮对话），并将重要的分析结果压缩提取至 `task.md` 作为长效记忆固化。

## 11. 运行与配置

### 11.1 统一启动方式

```bash
cd "d:\AI\Auto_System"
python main.py
```

访问: http://127.0.0.1:7860

### 11.2 桌面悬浮总控台（规划中）

```bash
cd "d:\AI\Auto_System"
python desktop_os.py
```

* 系统托盘图标管理
* 全局热键 (Alt+/ 切换显示)
* 无边框悬浮窗口
* 开机自启支持

### 11.3 配置说明

* **模型配置** (`config/models_config.json`): 管理 DeepSeek、Ollama、OpenAI、Claude 等 API 密钥与基础 URL。
* **Agent 配置** (`config/agents_config.json`): 定义 5 个 Agent 的系统提示词、技能偏好、激活状态。
* **工作空间** (`workspace/`): 包含 `task.md`（任务文档）、`exports/`（对话导出）、临时文件。
* **会话存储** (`sessions/`): 本地 JSON 文件存储历史会话，支持侧边栏加载。

## 12. 使用示例

### 示例 1: 创建并执行任务

1. **打开系统**: 运行 `python main.py`
2. **切换到助理面板**: 点击"助理"卡片或导航栏"Agents"
3. **描述需求**: 输入"帮我创建一个Python脚本，统计当前目录文件数量"
4. **生成任务**: 点击"生成任务"按钮，系统自动创建 `workspace/task.md`
5. **切换到极客面板**: 点击"极客"卡片
6. **执行任务**: 点击"执行任务"，系统自动执行并显示日志

### 示例 2: 直接与 Agent 对话

1. **选择任意 Agent 面板**
2. **输入问题**: 如"如何优化Python代码性能？"
3. **实时响应**: Agent 使用配置的 LLM 模型流式回答
4. **继续对话**: 基于上下文进行深入讨论

## 13. 故障排除

### 常见问题

1. **LLM 连接失败**: 检查 API 密钥和网络连接，验证 `config/models_config.json` 中模型是否激活。
2. **Open Interpreter 未安装**: 运行 `pip install open-interpreter`。
3. **端口冲突**: 确保 7860 端口未被占用，可修改 `main.py` 中的 `server_port`。
4. **模型未启用**: 在 `models_config.json` 中设置 `"active": true`。
5. **Unicode 编码错误**（Windows）: 避免在控制台输出特殊符号，使用 `[OK]` / `[ERROR]` 替代。

### 调试模式

```bash
# 启用详细日志
set GRADIO_DEBUG=1
python main.py
```

## 14. 贡献指南

1. 遵循现有代码风格和 Agent 通信纪律（文件级异步中转）。
2. 添加适当的注释和文档，更新本计划文档。
3. 测试响应式设计和跨平台兼容性（Windows/Linux/macOS）。
4. 确保向后兼容性，避免破坏现有配置。
5. 更新配置文档，保持 `config/` 目录下的 JSON 结构一致。

## 15. 文件说明

* `main.py` - 统一入口点，SPA 主应用（原 `app.py` / `glass_dashboard.py` 已废弃）
* `core/llm_engine.py` - LLM 引擎核心模块，支持流式生成
* `config/agents_config.json` - Agent 配置（5 个 Agent）
* `config/models_config.json` - 模型配置（多引擎支持）
* `workspace/` - 工作空间目录（任务文件、导出）
* `sessions/` - 会话存储目录
* `.gitignore` - 标准化忽略规则（排除环境、本地数据、OS 文件）

## 16. 设计特性

### Liquid Glass 效果

```css
backdrop-filter: blur(50px);
background: rgba(255, 255, 255, 0.3);
border: 1px solid rgba(0, 0, 0, 0.1);
box-shadow: inset 0px 4px 4px 0px rgba(255, 255, 255, 0.25);
```

### 颜色方案

* **Light 模式**:
  * 主色调: 电光蓝 (#0084FF)
  * 背景: 纯白色 (#FFFFFF)
  * 文字: 深黑色 (#000000)
  * 渐变: 浅蓝色 (#60B1FF → #319AFF)
* **Dark 模式**:
  * 主色调: 电光蓝 (#0084FF)
  * 背景: 深灰色 (#1a1a1a)
  * 文字: 浅灰色 (#f0f0f0)
  * 卡片背景: rgba(30, 30, 30, 0.6)

### 字体

* 标题: Fustat (Bold)
* 正文: Inter (Normal/Medium)
* 系统字体栈: 优先使用系统字体，无网络依赖

## 17. 技术实现细节

### 17.1 SPA 路由系统

* **核心函数**: `switch_panel(target_panel)` - 统一管理所有面板可见性
* **导航方式**:
  * 主页卡片点击: `gr.Button` 伪装为卡片，保留 `.click()` 事件
  * 导航栏按钮: 全局导航，支持 Home、Model、Agents、Settings
* **实现原理**: 使用 `gr.update(visible=True/False)` 控制面板显示/隐藏
* **优势**: 无页面刷新，保持应用状态，提升用户体验

### 17.2 主题切换系统

* **CSS 变量定义**: `:root` 中定义 Light/Dark 颜色方案变量
* **JavaScript 绑定**: 监听 `theme_toggle` Radio 组件变化
* **实时更新**: `document.documentElement.style.setProperty()` 动态更新 CSS 变量
* **即时反馈**: 无需页面重载，视觉变化立即生效

### 17.3 模型配置自动保存

* **触发机制**: 监听 API Key、Base URL 等输入框的 `.change()` 事件
* **保存逻辑**: 调用 `save_model_config()` 函数，更新 `config/models_config.json`
* **用户反馈**: 使用 `gr.Info()` 通知用户配置已保存
* **防重复提交**: 移除 `debounce` 参数（Gradio 不支持），避免事件冲突

### 17.4 Agent 通信协议

* **文件级中转**: `workspace/task.md` 作为唯一任务传递媒介
* **生成流程**: Assistant → 解析需求 → 写入 task.md → 标准化格式
* **执行流程**: Geek → 读取 task.md → Open Interpreter 执行 → 结果输出
* **优势**: 零 Token 消耗，避免 API 死循环，完全本地化

## 18. 下一步开发计划

1. **WebSocket 支持**: 实时双向通信，提升响应速度。
2. **音频分析流水线**: 集成 Librosa 实现 BPM 侦测、和弦提取。
3. **文档排版引擎**: 集成 Marp/Pandoc 实现 Markdown 转 PPT/PDF。
4. **插件系统**: 可扩展 Agent 架构，支持第三方插件。
5. **PWA 支持**: 离线应用能力，增强移动端体验。
6. **API 扩展**: 提供 REST API 接口，支持外部系统集成。
