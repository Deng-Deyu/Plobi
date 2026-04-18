# AI OS V4.0 - 统一液态玻璃智能系统

## 系统概述

AI OS V4.0 现已统一为一个完整的智能操作系统，融合了液态玻璃UI设计、真实LLM引擎集成和Open Interpreter自动化执行能力。系统遵循Agent异步通信纪律，Agent间通过workspace/task.md传递任务，禁止API直接对话。

## 核心功能

### 1. 真实LLM引擎集成 ✅
- **支持模型**: DeepSeek (OpenAI兼容)、Ollama本地模型、OpenAI、Claude
- **流式输出**: 所有Agent聊天均支持流式响应，实时显示生成过程
- **配置管理**: 通过config/models_config.json管理API密钥和模型配置
- **智能路由**: 自动为每个Agent选择最适合的模型

### 2. 助理Agent (👩‍💼 项目经理) ✅
- **任务文档生成**: 在对话中确认需求后，自动将任务要求写入workspace/task.md
- **Markdown格式化**: 按照标准格式生成任务文档（标题、描述、验收标准等）
- **需求追问**: 当需求不清晰时主动追问细节，确保任务完整可执行
- **实时对话**: 与用户进行自然语言交互，理解需求并转化为技术任务

### 3. 极客Agent (💻 自动化专家) ✅
- **Open Interpreter集成**: 自动执行workspace/task.md中的任务
- **任务执行**: 支持Python/Shell自动化操作
- **日志捕获**: 实时捕获terminal输出并展示在聊天框
- **安全执行**: 配置安全参数，避免破坏性操作

### 4. 液态玻璃UI设计 ✅
- **现代化界面**: 毛玻璃模糊效果、内阴影、高光效果
- **响应式布局**: 支持移动端和桌面端
- **英雄区域**: 吸引人的主页设计，渐变发光背景
- **玻璃效果面板**: 半透明玻璃材质，现代化卡片设计
- **流畅动画**: 悬停动画和过渡效果

## 系统架构

### Agent通信纪律
1. **禁止直接API对话**: Agent间不能直接调用对方API
2. **文件传递**: 通过workspace/task.md文件传递任务需求
3. **工作流**: 用户 → 助理Agent → task.md → 极客Agent → 执行结果
4. **异步处理**: 每个Agent独立工作，通过文件系统协调

### 技术栈
- **前端**: Gradio 6.0 (Python Web框架)
- **LLM引擎**: OpenAI兼容API (支持DeepSeek/Ollama/OpenAI/Claude)
- **自动化**: Open Interpreter (代码解释器)
- **桌面集成**: PyQt6 (桌面悬浮总控台)
- **UI设计**: 现代CSS (backdrop-filter, flexbox, 响应式设计)

## 运行方式

### 统一启动方式 (推荐)
```bash
cd "d:\AI\Auto_System"
python glass_dashboard.py
```
访问: http://127.0.0.1:7860

### 桌面悬浮总控台
```bash
cd "d:\AI\Auto_System"
python desktop_os.py
```
- 系统托盘图标管理
- 全局热键 (Alt+/ 切换显示)
- 无边框悬浮窗口
- 开机自启支持

### 独立英雄区域页面
直接打开 `hero_section.html` 在浏览器中查看纯HTML版本。

## 配置说明

### 1. 模型配置 (config/models_config.json)
```json
{
  "models": [
    {
      "id": "deepseek",
      "name": "DeepSeek",
      "api_key": "your_api_key_here",
      "api_base": "https://api.deepseek.com/v1",
      "active": true
    }
  ]
}
```

### 2. Agent配置 (config/agents_config.json)
- 每个Agent有独立的系统提示词和技能定义
- 模型偏好设置
- 激活状态管理

### 3. 工作空间 (workspace/)
- `task.md`: 任务文档存储
- `exports/`: 对话导出目录
- 临时文件存储

## 使用示例

### 示例1: 创建并执行任务
1. **打开系统**: 运行 `python glass_dashboard.py`
2. **切换到助理面板**: 点击"👩‍💼 助理"
3. **描述需求**: 输入"帮我创建一个Python脚本，统计当前目录文件数量"
4. **生成任务**: 点击"生成任务"按钮，系统自动创建task.md
5. **切换到极客面板**: 点击"💻 极客"
6. **执行任务**: 点击"🚀 执行任务"，系统自动执行并显示日志

### 示例2: 直接与Agent对话
1. **选择任意Agent面板**
2. **输入问题**: 如"如何优化Python代码性能？"
3. **实时响应**: Agent使用配置的LLM模型流式回答
4. **继续对话**: 基于上下文进行深入讨论

## 故障排除

### 常见问题
1. **LLM连接失败**: 检查API密钥和网络连接
2. **Open Interpreter未安装**: 运行 `pip install open-interpreter`
3. **端口冲突**: 确保7860端口未被占用
4. **模型未启用**: 在models_config.json中设置 `"active": true`

### 调试模式
```bash
# 启用详细日志
set GRADIO_DEBUG=1
python glass_dashboard.py
```

## 下一步开发计划

1. **WebSocket支持**: 实时双向通信
2. **深色模式**: 主题切换功能
3. **更多动画**: 微交互动画增强
4. **PWA支持**: 离线应用能力
5. **API扩展**: REST API接口
6. **插件系统**: 可扩展Agent架构

## 贡献指南

1. 遵循现有代码风格和Agent通信纪律
2. 添加适当的注释和文档
3. 测试响应式设计和跨平台兼容性
4. 确保向后兼容性
5. 更新配置文档

## 文件说明

- `app.py` - 修复后的原始AI OS应用
- `glass_dashboard.py` - 新液态玻璃风格仪表板
- `hero_section.html` - 独立英雄区域HTML页面
- `core/llm_engine.py` - LLM引擎核心模块
- `config/agents_config.json` - Agent配置
- `config/models_config.json` - 模型配置

## 设计特性

### 液态玻璃效果
  ```css
  backdrop-filter: blur(50px);
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: inset 0px 4px 4px 0px rgba(255, 255, 255, 0.25);
  ```

### 颜色方案
- 主色调: 电光蓝 (#0084FF)
- 背景: 纯白色 (#FFFFFF)
- 文字: 深黑色 (#000000)
- 渐变: 浅蓝色 (#60B1FF → #319AFF)

### 字体
- 标题: Fustat (Bold)
- 正文: Inter (Normal/Medium)

## 技术细节

### 修复的面板函数
1. `create_assistant_panel()` - 添加 `visible` 参数
2. `create_geek_panel()` - 添加 `visible` 参数  
3. `create_generic_agent_panel()` - 添加 `visible` 参数
4. `create_hr_panel()` - 添加 `visible` 参数
5. `create_model_panel()` - 添加 `visible` 参数

### 响应式设计
- 移动端优先设计
- 断点: 768px, 1024px
- 灵活网格布局
- 自适应字体大小

## 下一步建议

1. **性能优化**: 添加WebSocket支持实时更新
2. **主题切换**: 添加深色模式支持
3. **更多动画**: 增加微交互动画
4. **离线支持**: 添加PWA支持
5. **API扩展**: 扩展REST API接口

## 故障排除

### 常见问题
1. **端口冲突**: 确保7860和7861端口未被占用
2. **依赖缺失**: 运行 `pip install -r requirements.txt`
3. **代理问题**: 设置 `NO_PROXY` 环境变量
4. **字体加载**: 确保网络连接正常加载Google字体

### 调试模式
```bash
# 启用详细日志
set GRADIO_DEBUG=1
python app.py
```

## 贡献指南

1. 遵循现有代码风格
2. 添加适当的注释
3. 测试响应式设计
4. 确保向后兼容性
5. 更新配置文档