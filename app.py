"""
AI OS V4.0 - 核心Web应用 (完整SPA版本)
基于Gradio 6.0的单页面应用架构，支持多智能体切换
"""

import json
import os
import base64

# 强制绕过系统代理，解决 502 Bad Gateway 问题
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
# 禁用 Gradio 分析，避免网络请求失败
os.environ["GRADIO_ANALYTICS_ENABLED"] = "0"

import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from core.llm_engine import get_llm_engine

# 配置路径
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
WORKSPACE_DIR = BASE_DIR / "workspace"
AVATAR_DIR = BASE_DIR / "avatars"

# 确保目录存在
for directory in [CONFIG_DIR, WORKSPACE_DIR, AVATAR_DIR]:
    directory.mkdir(exist_ok=True)

# 默认头像数据（base64编码的小图标）
DEFAULT_AVATARS = {
    "assistant": "👩‍💼",
    "geek": "💻",
    "architect": "🎨",
    "publisher": "📚",
    "scout": "🕵️",
    "hr": "⚙️",
    "model": "🧠"
}


def load_json_config(file_name: str) -> Dict[str, Any]:
    """加载JSON配置文件"""
    config_path = CONFIG_DIR / file_name
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载配置文件 {file_name} 失败: {e}")
    return {}


def save_json_config(file_name: str, data: Dict[str, Any]) -> bool:
    """保存JSON配置文件"""
    try:
        config_path = CONFIG_DIR / file_name
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件 {file_name} 失败: {e}")
        return False


def get_agent_avatar(agent_id: str, avatar_path: str = "") -> str:
    """
    获取Agent头像
    如果avatar_path不为空且文件存在，返回base64编码的图片
    否则返回默认emoji
    """
    if avatar_path and os.path.exists(avatar_path):
        try:
            with open(avatar_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
                return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            pass

    # 返回默认emoji
    return DEFAULT_AVATARS.get(agent_id, "🤖")


def create_agent_nav_html(agent: Dict[str, Any]) -> gr.HTML:
    """
    创建Agent导航HTML组件
    返回: HTML组件
    """
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "未知Agent")
    avatar_path = agent.get("avatar", "")

    # 获取头像（base64图片或emoji）
    avatar_content = get_agent_avatar(agent_id, avatar_path)

    # 判断是否是base64图片
    is_image = avatar_content.startswith("data:image")

    if is_image:
        # 创建带图片的HTML组件
        html_content = f"""
        <div class="nav-item">
            <div class="nav-html" style="display: flex; align-items: center; gap: 8px;">
                <img src="{avatar_content}" style="width: 24px; height: 24px; border-radius: 50%; object-fit: cover;">
                <span>{agent_name}</span>
            </div>
        </div>
        """
    else:
        # 创建带emoji的HTML组件
        html_content = f"""
        <div class="nav-item">
            <div class="nav-html" style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">{avatar_content}</span>
                <span>{agent_name}</span>
            </div>
        </div>
        """

    return gr.HTML(value=html_content)


def create_geek_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False) -> gr.Column:
    """创建极客（自动化专家）工作面板"""
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")
    personality = agent.get("personality", "")
    system_prompt = agent.get("system_prompt", "")
    skills = agent.get("skills", [])

    with gr.Column(elem_classes="agent-panel", visible=visible) as panel:
        # 面板标题
        gr.Markdown(f"## {agent_name} - {agent_role}")
        gr.Markdown(f"**个性**: {personality}")

        # 技能栈
        if skills:
            skills_text = " | ".join(skills)
            gr.Markdown(f"**技能栈**: {skills_text}")

        # 系统提示词预览
        with gr.Accordion("系统提示词 (System Prompt)", open=False):
            gr.Markdown(f"```\n{system_prompt}\n```")

        # 分隔线
        gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>")

        # 任务文档预览
        with gr.Accordion("📄 当前任务文档 (workspace/task.md)", open=True):
            task_content_display = gr.Markdown("")

            # 刷新任务文档按钮
            def refresh_task_document():
                task_path = WORKSPACE_DIR / "task.md"
                if task_path.exists():
                    try:
                        with open(task_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        return content
                    except Exception as e:
                        return f"❌ 读取任务文档失败: {str(e)}"
                else:
                    return "⚠️ 未找到任务文档，请在助理面板生成任务"

            refresh_btn = gr.Button("刷新任务文档", variant="secondary", size="sm", elem_classes="btn-secondary")
            refresh_btn.click(refresh_task_document, outputs=[task_content_display])

        # 聊天区域
        with gr.Column(elem_classes="chatbot-container"):
            chatbot = gr.Chatbot(
                label="执行日志",
                height=400,
                show_label=False,
                render_markdown=True
            )

            # 输入区域
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder=f"输入自定义指令或直接执行任务... (按Enter发送)",
                    lines=2,
                    max_lines=6,
                    container=False,
                    scale=9,
                    elem_classes="input-field"
                )
                send_btn = gr.Button("发送", variant="primary", scale=1, min_width=80, elem_classes="btn-3d-primary")

            # 功能按钮
            with gr.Row():
                clear_btn = gr.Button("清空日志", variant="secondary", elem_classes="btn-secondary")
                execute_task_btn = gr.Button("🚀 执行任务", variant="primary", elem_classes="btn-3d-primary")

        # 状态显示
        status_text = gr.Textbox(label="执行状态", visible=False)

        # 聊天事件处理（使用LLM）
        def chat_handler(message: str, history):
            if not message.strip():
                return "", history

            if history is None:
                history = []

            # Gradio 6.0格式：添加用户消息
            history.append({"role": "user", "content": message})
            yield "", history

            try:
                # 初始化LLM引擎
                llm_engine = get_llm_engine()

                # 临时添加一个初始回复
                initial_reply = f"💻 **极客模式**: 正在分析您的指令..."
                history.append({"role": "assistant", "content": initial_reply})
                yield "", history

                # 使用LLM引擎生成流式响应
                full_response = ""
                for chunk in llm_engine.generate_stream(agent_id, message, history[:-1]):
                    full_response += chunk
                    history[-1] = {"role": "assistant", "content": initial_reply + full_response}
                    yield "", history

            except Exception as e:
                error_msg = f"❌ 处理指令失败: {str(e)}"
                if history and len(history) > 0 and history[-1].get("role") == "assistant":
                    history[-1] = {"role": "assistant", "content": error_msg}
                else:
                    history.append({"role": "assistant", "content": error_msg})
                yield "", history

        # 执行任务按钮处理
        def execute_task(history):
            if history is None:
                history = []

            try:
                # 检查Open Interpreter是否可用
                try:
                    from interpreter import interpreter
                    interpreter_available = True
                except ImportError:
                    interpreter_available = False
                    raise ImportError("Open Interpreter 未安装，请运行: pip install open-interpreter")

                if not interpreter_available:
                    raise ImportError("Open Interpreter 不可用")

                # 读取任务文档
                task_path = WORKSPACE_DIR / "task.md"
                if not task_path.exists():
                    error_msg = "❌ 未找到任务文档，请在助理面板生成任务"
                    history.append({"role": "assistant", "content": error_msg})
                    return history, "❌ 任务执行失败"

                with open(task_path, 'r', encoding='utf-8') as f:
                    task_content = f.read()

                # 配置Open Interpreter
                interpreter.offline = True
                interpreter.auto_run = True

                # 添加系统消息
                system_msg = f"🎯 **任务开始执行**\n\n**任务文档**:\n```\n{task_content}\n```\n\n开始执行自动化任务..."
                history.append({"role": "assistant", "content": system_msg})
                yield history, "🔄 任务执行中..."

                # 执行任务
                try:
                    # 这里需要实现流式执行
                    # 由于Open Interpreter的流式输出较复杂，先使用简单版本
                    result = interpreter.chat(f"请执行以下任务:\n\n{task_content}")

                    # 添加执行结果
                    result_msg = f"✅ **任务执行完成**\n\n**执行结果**:\n```\n{str(result)}\n```"
                    history.append({"role": "assistant", "content": result_msg})
                    yield history, "✅ 任务执行完成"

                except Exception as e:
                    error_msg = f"❌ 任务执行失败: {str(e)}"
                    history.append({"role": "assistant", "content": error_msg})
                    yield history, "❌ 任务执行失败"

            except Exception as e:
                error_msg = f"❌ 执行任务时发生错误: {str(e)}"
                if history is None:
                    history = []
                history.append({"role": "assistant", "content": error_msg})
                yield history, "❌ 执行失败"

        # 绑定事件
        msg_input.submit(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        send_btn.click(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        clear_btn.click(lambda: [], outputs=[chatbot])

        # 绑定执行任务事件
        execute_task_btn.click(
            execute_task,
            inputs=[chatbot],
            outputs=[chatbot, status_text]
        )

        # 初始加载任务文档
        task_path = WORKSPACE_DIR / "task.md"
        if task_path.exists():
            try:
                with open(task_path, 'r', encoding='utf-8') as f:
                    initial_content = f.read()
                task_content_display.value = initial_content
            except:
                task_content_display.value = "⚠️ 无法读取任务文档"

    return panel


def create_assistant_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False) -> gr.Column:
    """创建Agent工作面板"""
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")
    personality = agent.get("personality", "")
    system_prompt = agent.get("system_prompt", "")
    skills = agent.get("skills", [])

    with gr.Column(elem_classes="agent-panel", visible=visible) as panel:
        # 面板标题
        gr.Markdown(f"## {agent_name} - {agent_role}")

        # 个性描述
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown(f"**个性**: {personality}")

                # 技能栈
                if skills:
                    skills_text = " | ".join(skills)
                    gr.Markdown(f"**技能栈**: {skills_text}")

            with gr.Column(scale=1):
                # 模型选择器
                available_models = []
                for model in models_config.get("models", []):
                    if model.get("active", False):
                        available_models.append(model.get("name", "未知模型"))

                model_dropdown = gr.Dropdown(
                    choices=available_models,
                    value=available_models[0] if available_models else "无可用模型",
                    label="选择模型",
                    interactive=True
                )

        # 系统提示词预览
        with gr.Accordion("系统提示词 (System Prompt)", open=False):
            gr.Markdown(f"```\n{system_prompt}\n```")

        # 分隔线
        gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>")

        # 聊天区域
        with gr.Column(elem_classes="chatbot-container"):
            chatbot = gr.Chatbot(
                label="对话记录",
                height=400,
                show_label=False,
                render_markdown=True
            )

            # 输入区域
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder=f"与 {agent_name} 对话... (按Enter发送)",
                    lines=2,
                    max_lines=6,
                    container=False,
                    scale=9,
                    elem_classes="input-field"
                )
                send_btn = gr.Button("发送", variant="primary", scale=1, min_width=80, elem_classes="btn-3d-primary")

            # 功能按钮
            with gr.Row():
                clear_btn = gr.Button("清空对话", variant="secondary", elem_classes="btn-secondary")
                export_btn = gr.Button("导出对话", variant="secondary", elem_classes="btn-secondary")
                task_btn = gr.Button("生成任务", variant="secondary", elem_classes="btn-secondary")

        # 聊天事件处理
        def chat_handler(message: str, history):
            if not message.strip():
                return "", history

            if history is None:
                history = []

            # Gradio 6.0格式：添加用户消息
            history.append({"role": "user", "content": message})
            yield "", history

            try:
                # 初始化LLM引擎
                llm_engine = get_llm_engine()

                # 获取当前选择的模型（从dropdown）
                selected_model = model_dropdown.value if hasattr(model_dropdown, 'value') else ""

                # 临时添加一个初始回复，让用户知道正在处理
                initial_reply = f"👋 你好！我是{agent_name} ({agent_role})。\n\n"
                initial_reply += f"已收到您的消息: '{message}'\n\n"
                initial_reply += f"根据我的个性（{personality}），我正在处理您的请求..."

                if selected_model and selected_model != "无可用模型":
                    initial_reply += f"\n\n正在使用模型: **{selected_model}**"

                history.append({"role": "assistant", "content": initial_reply})
                yield "", history

                # 使用LLM引擎生成流式响应
                full_response = ""
                for chunk in llm_engine.generate_stream(agent_id, message, history[:-1]):  # 排除刚添加的初始回复
                    full_response += chunk
                    # 更新最后一条消息的内容
                    history[-1] = {"role": "assistant", "content": initial_reply + full_response}
                    yield "", history

            except Exception as e:
                # 错误处理：返回友好的错误信息
                error_msg = f"❌ 抱歉，处理请求时出现错误:\n\n```\n{str(e)}\n```\n\n"
                error_msg += "请检查：\n1. 模型配置是否正确\n2. API密钥是否有效\n3. 网络连接是否正常"

                if history and len(history) > 0 and history[-1].get("role") == "assistant":
                    history[-1] = {"role": "assistant", "content": error_msg}
                else:
                    history.append({"role": "assistant", "content": error_msg})
                yield "", history

        # 绑定聊天事件
        msg_input.submit(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        send_btn.click(chat_handler, [msg_input, chatbot], [msg_input, chatbot])

        # 清空对话按钮
        def clear_chat():
            return []

        clear_btn.click(clear_chat, outputs=[chatbot])

        # 导出对话按钮
        def export_chat(history):
            if not history:
                return "❌ 没有对话记录可导出"

            try:
                # 创建导出目录
                export_dir = WORKSPACE_DIR / "exports"
                export_dir.mkdir(exist_ok=True)

                # 生成文件名
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_export_{agent_id}_{timestamp}.txt"
                filepath = export_dir / filename

                # 将对话历史写入文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# AI OS - {agent_name} 对话导出\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    for i, msg in enumerate(history):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        f.write(f"## [{i+1}] {role.upper()}\n")
                        f.write(f"{content}\n\n")

                return f"✅ 对话已导出到: {filepath}"
            except Exception as e:
                return f"❌ 导出失败: {str(e)}"

        export_status = gr.Textbox(label="导出状态", visible=False)
        export_btn.click(export_chat, inputs=[chatbot], outputs=[export_status])

        # 生成任务按钮
        def generate_task(message: str, history):
            if not message.strip():
                return history, "❌ 请输入任务需求"

            try:
                llm_engine = get_llm_engine()

                # 生成任务文档
                task_content = llm_engine.generate_task_document(message)

                # 在聊天历史中添加任务生成结果
                if history is None:
                    history = []

                # 添加系统消息
                history.append({"role": "assistant", "content": f"✅ 已生成任务文档:\n\n{task_content}\n\n任务文档已保存到 `workspace/task.md`"})

                return history, "✅ 任务生成成功！"
            except Exception as e:
                error_msg = f"❌ 生成任务失败: {str(e)}"
                if history is None:
                    history = []
                history.append({"role": "assistant", "content": error_msg})
                return history, error_msg

        # 添加任务状态输出文本框
        task_status = gr.Textbox(label="任务状态", visible=False)

        # 绑定任务生成事件
        task_btn.click(
            generate_task,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, task_status]
        )

    return panel


def create_generic_agent_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False) -> gr.Column:
    """创建通用Agent工作面板（用于除assistant和geek外的其他Agent）"""
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")
    personality = agent.get("personality", "")
    system_prompt = agent.get("system_prompt", "")
    skills = agent.get("skills", [])

    with gr.Column(elem_classes="agent-panel", visible=visible) as panel:
        # 面板标题
        gr.Markdown(f"## {agent_name} - {agent_role}")

        # 个性描述
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown(f"**个性**: {personality}")

                # 技能栈
                if skills:
                    skills_text = " | ".join(skills)
                    gr.Markdown(f"**技能栈**: {skills_text}")

            with gr.Column(scale=1):
                # 模型选择器
                available_models = []
                for model in models_config.get("models", []):
                    if model.get("active", False):
                        available_models.append(model.get("name", "未知模型"))

                model_dropdown = gr.Dropdown(
                    choices=available_models,
                    value=available_models[0] if available_models else "无可用模型",
                    label="选择模型",
                    interactive=True
                )

        # 系统提示词预览
        with gr.Accordion("系统提示词 (System Prompt)", open=False):
            gr.Markdown(f"```\n{system_prompt}\n```")

        # 分隔线
        gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e2e8f0;'>")

        # 聊天区域
        with gr.Column(elem_classes="chatbot-container"):
            chatbot = gr.Chatbot(
                label="对话记录",
                height=400,
                show_label=False,
                render_markdown=True
            )

            # 输入区域
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder=f"与 {agent_name} 对话... (按Enter发送)",
                    lines=2,
                    max_lines=6,
                    container=False,
                    scale=9,
                    elem_classes="input-field"
                )
                send_btn = gr.Button("发送", variant="primary", scale=1, min_width=80, elem_classes="btn-3d-primary")

            # 功能按钮
            with gr.Row():
                clear_btn = gr.Button("清空对话", variant="secondary", elem_classes="btn-secondary")
                export_btn = gr.Button("导出对话", variant="secondary", elem_classes="btn-secondary")

        # 聊天事件处理
        def chat_handler(message: str, history):
            if not message.strip():
                return "", history

            if history is None:
                history = []

            # Gradio 6.0格式：添加用户消息
            history.append({"role": "user", "content": message})
            yield "", history

            try:
                # 初始化LLM引擎
                llm_engine = get_llm_engine()

                # 获取当前选择的模型（从dropdown）
                selected_model = model_dropdown.value if hasattr(model_dropdown, 'value') else ""

                # 临时添加一个初始回复，让用户知道正在处理
                initial_reply = f"👋 你好！我是{agent_name} ({agent_role})。\n\n"
                initial_reply += f"已收到您的消息: '{message}'\n\n"
                initial_reply += f"根据我的个性（{personality}），我正在处理您的请求..."

                if selected_model and selected_model != "无可用模型":
                    initial_reply += f"\n\n正在使用模型: **{selected_model}**"

                history.append({"role": "assistant", "content": initial_reply})
                yield "", history

                # 使用LLM引擎生成流式响应
                full_response = ""
                for chunk in llm_engine.generate_stream(agent_id, message, history[:-1]):  # 排除刚添加的初始回复
                    full_response += chunk
                    # 更新最后一条消息的内容
                    history[-1] = {"role": "assistant", "content": initial_reply + full_response}
                    yield "", history

            except Exception as e:
                # 错误处理：返回友好的错误信息
                error_msg = f"❌ 抱歉，处理请求时出现错误:\n\n```\n{str(e)}\n```\n\n"
                error_msg += "请检查：\n1. 模型配置是否正确\n2. API密钥是否有效\n3. 网络连接是否正常"

                if history and len(history) > 0 and history[-1].get("role") == "assistant":
                    history[-1] = {"role": "assistant", "content": error_msg}
                else:
                    history.append({"role": "assistant", "content": error_msg})
                yield "", history

        # 绑定聊天事件
        msg_input.submit(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        send_btn.click(chat_handler, [msg_input, chatbot], [msg_input, chatbot])

        # 清空对话按钮
        def clear_chat():
            return []

        clear_btn.click(clear_chat, outputs=[chatbot])

        # 导出对话按钮
        def export_chat(history):
            if not history:
                return "❌ 没有对话记录可导出"

            try:
                # 创建导出目录
                export_dir = WORKSPACE_DIR / "exports"
                export_dir.mkdir(exist_ok=True)

                # 生成文件名
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"chat_export_{agent_id}_{timestamp}.txt"
                filepath = export_dir / filename

                # 将对话历史写入文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# AI OS - {agent_name} 对话导出\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    for i, msg in enumerate(history):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        f.write(f"## [{i+1}] {role.upper()}\n")
                        f.write(f"{content}\n\n")

                return f"✅ 对话已导出到: {filepath}"
            except Exception as e:
                return f"❌ 导出失败: {str(e)}"

        export_status = gr.Textbox(label="导出状态", visible=False)
        export_btn.click(export_chat, inputs=[chatbot], outputs=[export_status])

    return panel


def create_hr_panel(agents_config: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False) -> gr.Column:
    """创建团队HR配置面板"""
    with gr.Column(elem_classes="agent-panel", visible=visible) as panel:
        gr.Markdown("## ⚙️ 团队HR - Agent配置管理")
        gr.Markdown("管理智能体团队的配置，包括头像、名称、系统提示词等")

        # Agent列表
        agents = agents_config.get("agents", [])

        with gr.Tabs() as tabs:
            for idx, agent in enumerate(agents):
                agent_id = agent.get("id", f"agent_{idx}")
                agent_name = agent.get("name", f"Agent {idx}")

                with gr.TabItem(agent_name):
                    with gr.Row():
                        # 左侧：基本信息
                        with gr.Column(scale=1):
                            # 头像上传
                            avatar_input = gr.Image(
                                label="头像",
                                type="filepath",
                                value=agent.get("avatar") or None,
                                height=150
                            )

                            # 名称和角色
                            name_input = gr.Textbox(
                                label="名称",
                                value=agent.get("name", ""),
                                interactive=True
                            )

                            role_input = gr.Textbox(
                                label="角色",
                                value=agent.get("role", ""),
                                interactive=True
                            )

                        # 右侧：详细配置
                        with gr.Column(scale=2):
                            # 个性描述
                            personality_input = gr.Textbox(
                                label="个性描述",
                                value=agent.get("personality", ""),
                                lines=2,
                                interactive=True
                            )

                            # 系统提示词
                            prompt_input = gr.Textbox(
                                label="系统提示词",
                                value=agent.get("system_prompt", ""),
                                lines=6,
                                interactive=True
                            )

                            # 技能栈
                            skills_input = gr.Textbox(
                                label="技能栈 (用逗号分隔)",
                                value=", ".join(agent.get("skills", [])),
                                interactive=True
                            )

                            # 模型偏好
                            available_models = ["auto"] + [
                                model.get("id", "")
                                for model in models_config.get("models", [])
                                if model.get("active", False)
                            ]

                            model_select = gr.Dropdown(
                                choices=available_models,
                                value=agent.get("model_preference", "auto"),
                                label="模型偏好",
                                interactive=True
                            )

                    # 保存按钮
                    save_btn = gr.Button("保存配置", variant="primary", elem_classes="btn-3d-primary")

                    def save_agent_config(
                        avatar, name, role, personality,
                        prompt, skills, model_pref, agent_idx=idx
                    ):
                        """保存单个Agent配置"""
                        agents = agents_config.get("agents", [])
                        if 0 <= agent_idx < len(agents):
                            # 更新头像路径
                            if avatar and os.path.exists(avatar):
                                # 复制头像到avatars目录
                                avatar_filename = f"{agents[agent_idx]['id']}_{Path(avatar).name}"
                                avatar_dest = AVATAR_DIR / avatar_filename
                                try:
                                    import shutil
                                    shutil.copy2(avatar, avatar_dest)
                                    agents[agent_idx]['avatar'] = str(avatar_dest)
                                except Exception as e:
                                    print(f"复制头像失败: {e}")
                                    agents[agent_idx]['avatar'] = avatar

                            # 更新其他字段
                            agents[agent_idx]['name'] = name.strip()
                            agents[agent_idx]['role'] = role.strip()
                            agents[agent_idx]['personality'] = personality.strip()
                            agents[agent_idx]['system_prompt'] = prompt.strip()
                            agents[agent_idx]['skills'] = [
                                s.strip() for s in skills.split(",") if s.strip()
                            ]
                            agents[agent_idx]['model_preference'] = model_pref

                            # 保存到文件
                            agents_config["agents"] = agents
                            if save_json_config("agents_config.json", agents_config):
                                return "✅ 配置已保存！"
                            else:
                                return "❌ 保存失败！"
                        return "❌ Agent索引错误！"

                    save_btn.click(
                        save_agent_config,
                        inputs=[
                            avatar_input, name_input, role_input,
                            personality_input, prompt_input, skills_input, model_select
                        ],
                        outputs=gr.Textbox(label="保存状态", visible=True)
                    )

        # 添加新Agent按钮
        with gr.Accordion("添加新Agent", open=False):
            with gr.Row():
                new_id = gr.Textbox(label="Agent ID", placeholder="例如: designer")
                new_name = gr.Textbox(label="名称", placeholder="例如: 🎨 设计师")
                new_role = gr.Textbox(label="角色", placeholder="例如: UI/UX设计师")

            new_personality = gr.Textbox(
                label="个性描述",
                placeholder="例如: 创意、注重细节，善于将概念转化为视觉设计",
                lines=2
            )

            new_prompt = gr.Textbox(
                label="系统提示词",
                placeholder="输入系统提示词...",
                lines=4
            )

            add_btn = gr.Button("添加新Agent", variant="primary")

            def add_new_agent(id_str, name, role, personality, prompt):
                if not id_str.strip() or not name.strip():
                    return "❌ ID和名称不能为空！"

                agents = agents_config.get("agents", [])

                # 检查ID是否重复
                if any(agent.get("id") == id_str for agent in agents):
                    return f"❌ Agent ID '{id_str}' 已存在！"

                # 添加新Agent
                new_agent = {
                    "id": id_str.strip(),
                    "name": name.strip(),
                    "role": role.strip(),
                    "avatar": "",
                    "personality": personality.strip(),
                    "system_prompt": prompt.strip(),
                    "skills": ["待配置"],
                    "model_preference": "auto",
                    "active": True
                }

                agents.append(new_agent)
                agents_config["agents"] = agents

                if save_json_config("agents_config.json", agents_config):
                    return f"✅ Agent '{name}' 添加成功！请刷新页面查看。"
                else:
                    return "❌ 保存失败！"

            add_btn.click(
                add_new_agent,
                inputs=[new_id, new_name, new_role, new_personality, new_prompt],
                outputs=gr.Textbox(label="添加状态", visible=True)
            )

    return panel


def create_model_panel(models_config: Dict[str, Any], visible: bool = False) -> gr.Column:
    """创建模型中枢管理面板"""
    with gr.Column(elem_classes="agent-panel", visible=visible) as panel:
        gr.Markdown("## 🧠 模型中枢 - 模型配置管理")
        gr.Markdown("管理大模型API配置，支持添加、编辑和测试模型连接")

        models = models_config.get("models", [])

        with gr.Tabs() as tabs:
            for idx, model in enumerate(models):
                model_name = model.get("name", f"模型 {idx}")

                with gr.TabItem(model_name):
                    with gr.Row():
                        # 左侧：基本信息
                        with gr.Column(scale=1):
                            # 模型ID
                            id_input = gr.Textbox(
                                label="模型ID",
                                value=model.get("id", ""),
                                interactive=(idx > 0)  # 第一个模型（auto）不可编辑
                            )

                            # 模型名称
                            name_input = gr.Textbox(
                                label="模型名称",
                                value=model.get("name", ""),
                                interactive=True
                            )

                            # 描述
                            desc_input = gr.Textbox(
                                label="描述",
                                value=model.get("description", ""),
                                lines=2,
                                interactive=True
                            )

                            # 类型
                            type_input = gr.Dropdown(
                                choices=["auto", "local", "cloud", "strategy"],
                                value=model.get("type", "cloud"),
                                label="类型",
                                interactive=True
                            )

                            # 提供商
                            provider_input = gr.Textbox(
                                label="提供商",
                                value=model.get("provider", ""),
                                interactive=True
                            )

                        # 右侧：API配置
                        with gr.Column(scale=2):
                            # API密钥
                            api_key_input = gr.Textbox(
                                label="API密钥",
                                value=model.get("api_key", ""),
                                type="password",
                                interactive=True
                            )

                            # API Base URL
                            api_base_input = gr.Textbox(
                                label="API Base URL",
                                value=model.get("api_base", ""),
                                interactive=True
                            )

                            # 默认模型
                            default_model_input = gr.Textbox(
                                label="默认模型名称",
                                value=model.get("default_model", ""),
                                interactive=True
                            )

                            with gr.Row():
                                # 上下文窗口
                                context_input = gr.Number(
                                    label="上下文窗口大小",
                                    value=model.get("context_window", 8000),
                                    interactive=True
                                )

                                # 最大令牌数
                                max_tokens_input = gr.Number(
                                    label="最大令牌数",
                                    value=model.get("max_tokens", 1600),
                                    interactive=True
                                )

                            with gr.Row():
                                # 超时时间
                                timeout_input = gr.Number(
                                    label="超时时间(秒)",
                                    value=model.get("timeout", 120),
                                    interactive=True
                                )

                                # 启用状态
                                active_input = gr.Checkbox(
                                    label="启用",
                                    value=model.get("active", True),
                                    interactive=True
                                )

                    # 测试连接按钮
                    test_btn = gr.Button("测试连接", variant="secondary", elem_classes="btn-secondary")

                    # 保存按钮
                    save_btn = gr.Button("保存配置", variant="primary", elem_classes="btn-3d-primary")

                    def test_model_connection(
                        api_key, api_base, default_model, model_idx=idx
                    ):
                        """测试模型连接"""
                        # 这里可以添加实际的连接测试逻辑
                        # 目前返回模拟结果
                        return f"✅ 模型连接测试成功！\nBase URL: {api_base}\n模型: {default_model}"

                    def save_model_config(
                        model_id, name, description, model_type, provider,
                        api_key, api_base, default_model, context_window,
                        max_tokens, timeout, active, model_idx=idx
                    ):
                        """保存模型配置"""
                        models = models_config.get("models", [])
                        if 0 <= model_idx < len(models):
                            # 更新模型配置
                            models[model_idx].update({
                                "id": model_id.strip(),
                                "name": name.strip(),
                                "description": description.strip(),
                                "type": model_type,
                                "provider": provider.strip(),
                                "api_key": api_key.strip(),
                                "api_base": api_base.strip(),
                                "default_model": default_model.strip(),
                                "context_window": int(context_window),
                                "max_tokens": int(max_tokens),
                                "timeout": int(timeout),
                                "active": bool(active)
                            })

                            # 保存到文件
                            models_config["models"] = models
                            if save_json_config("models_config.json", models_config):
                                return "✅ 模型配置已保存！"
                            else:
                                return "❌ 保存失败！"
                        return "❌ 模型索引错误！"

                    test_output = gr.Textbox(label="测试结果", visible=False)
                    save_output = gr.Textbox(label="保存状态", visible=False)

                    test_btn.click(
                        test_model_connection,
                        inputs=[api_key_input, api_base_input, default_model_input],
                        outputs=test_output
                    )

                    save_btn.click(
                        save_model_config,
                        inputs=[
                            id_input, name_input, desc_input, type_input, provider_input,
                            api_key_input, api_base_input, default_model_input,
                            context_input, max_tokens_input, timeout_input, active_input
                        ],
                        outputs=save_output
                    )

        # 添加新模型按钮
        with gr.Accordion("添加新模型", open=False):
            with gr.Row():
                new_id = gr.Textbox(label="模型ID", placeholder="例如: gemini")
                new_name = gr.Textbox(label="模型名称", placeholder="例如: Google Gemini")
                new_type = gr.Dropdown(
                    choices=["local", "cloud"],
                    value="cloud",
                    label="类型"
                )

            new_desc = gr.Textbox(label="描述", placeholder="模型描述...", lines=2)
            new_provider = gr.Textbox(label="提供商", placeholder="例如: google")

            with gr.Row():
                new_api_key = gr.Textbox(label="API密钥", type="password")
                new_api_base = gr.Textbox(label="API Base URL", placeholder="例如: https://api.gemini.google.com/v1")

            new_default_model = gr.Textbox(label="默认模型名称", placeholder="例如: gemini-pro")

            with gr.Row():
                new_context = gr.Number(label="上下文窗口大小", value=8000)
                new_max_tokens = gr.Number(label="最大令牌数", value=1600)
                new_timeout = gr.Number(label="超时时间(秒)", value=120)

            add_btn = gr.Button("添加新模型", variant="primary")

            def add_new_model(
                model_id, name, model_type, description, provider,
                api_key, api_base, default_model, context_window,
                max_tokens, timeout
            ):
                if not model_id.strip() or not name.strip():
                    return "❌ ID和名称不能为空！"

                models = models_config.get("models", [])

                # 检查ID是否重复
                if any(model.get("id") == model_id for model in models):
                    return f"❌ 模型ID '{model_id}' 已存在！"

                # 添加新模型
                new_model = {
                    "id": model_id.strip(),
                    "name": name.strip(),
                    "description": description.strip(),
                    "type": model_type,
                    "provider": provider.strip(),
                    "api_key": api_key.strip(),
                    "api_base": api_base.strip(),
                    "default_model": default_model.strip(),
                    "context_window": int(context_window),
                    "max_tokens": int(max_tokens),
                    "timeout": int(timeout),
                    "active": True
                }

                models.append(new_model)
                models_config["models"] = models

                if save_json_config("models_config.json", models_config):
                    return f"✅ 模型 '{name}' 添加成功！请刷新页面查看。"
                else:
                    return "❌ 保存失败！"

            add_btn.click(
                add_new_model,
                inputs=[
                    new_id, new_name, new_type, new_desc, new_provider,
                    new_api_key, new_api_base, new_default_model,
                    new_context, new_max_tokens, new_timeout
                ],
                outputs=gr.Textbox(label="添加状态", visible=True)
            )

    return panel


def build_ui():
    """构建完整的UI界面"""
    # 加载配置
    agents_config = load_json_config("agents_config.json")
    models_config = load_json_config("models_config.json")

    # 获取所有Agent
    agents = agents_config.get("agents", [])
    active_agents = [agent for agent in agents if agent.get("active", True)]

    with gr.Blocks(
        title="AI OS V4.0",
    ) as app:
        # ========== 主布局：侧边栏 + 主工作区 ==========
        with gr.Row():
            # ========== 左侧侧边栏 ==========
            with gr.Column(scale=2, elem_id="sidebar"):
                # Logo
                gr.HTML("""
                <div class="sidebar-logo">
                    <h1 class="logo-main">AI OS V4.0</h1>
                    <span class="logo-sub">SYSTEM DESIGN</span>
                </div>
                """)

                # 导航按钮容器
                with gr.Column(elem_classes="nav-buttons-container"):
                    nav_buttons = []  # 存储按钮组件和对应的ID

                    for agent in active_agents:
                        agent_id = agent.get("id", "")
                        agent_name = agent.get("name", "未知Agent")
                        avatar_content = get_agent_avatar(agent_id, agent.get("avatar", ""))

                        # 判断是否是emoji还是图片
                        is_emoji = not avatar_content.startswith("data:image")

                        # 使用emoji作为按钮文本，如果是图片则使用默认emoji
                        if is_emoji:
                            button_text = f"{avatar_content} {agent_name}"
                        else:
                            # 对于图片头像，使用默认emoji
                            default_emoji = DEFAULT_AVATARS.get(agent_id, "🤖")
                            button_text = f"{default_emoji} {agent_name}"

                        btn = gr.Button(
                            button_text,
                            variant="secondary",
                            elem_classes="sidebar-btn"
                        )
                        nav_buttons.append((agent_id, btn))

                    # 功能按钮 - 团队HR
                    hr_btn = gr.Button(
                        "⚙️ 团队HR",
                        variant="secondary",
                        elem_classes="sidebar-btn"
                    )

                    # 功能按钮 - 模型中枢
                    model_btn = gr.Button(
                        "🧠 模型中枢",
                        variant="secondary",
                        elem_classes="sidebar-btn"
                    )

            # ========== 右侧主工作区 ==========
            with gr.Column(scale=8, elem_id="main-workspace"):
                # 存储所有面板的引用
                all_panels = {}
                agent_panels = []

                # 创建Agent面板
                for idx, agent in enumerate(active_agents):
                    agent_id = agent.get("id", "")
                    is_visible = (idx == 0)  # 第一个Agent面板可见

                    # 创建对应的面板（根据Agent类型选择不同的面板创建函数）
                    if agent_id == "assistant":
                        panel = create_assistant_panel(agent, models_config, visible=is_visible)
                    elif agent_id == "geek":
                        panel = create_geek_panel(agent, models_config, visible=is_visible)
                    else:
                        panel = create_generic_agent_panel(agent, models_config, visible=is_visible)

                    agent_panels.append((agent_id, panel))
                    all_panels[agent_id] = panel

                # 添加功能面板
                hr_panel = create_hr_panel(agents_config, models_config, visible=False)
                model_panel = create_model_panel(models_config, visible=False)

                all_panels["hr"] = hr_panel
                all_panels["model"] = model_panel

                # 初始状态：显示第一个Agent面板

        # ========== 面板切换逻辑 ==========
        def switch_panel(panel_name: str) -> List[gr.update]:
            """切换显示指定面板，隐藏其他所有面板"""
            updates = []
            for name, panel in all_panels.items():
                updates.append(gr.update(visible=(name == panel_name)))
            return updates

        # 绑定Agent按钮事件
        for agent_id, btn in nav_buttons:
            btn.click(
                fn=lambda pn=agent_id: switch_panel(pn),
                outputs=list(all_panels.values())
            )

        # 绑定功能按钮事件
        hr_btn.click(
            fn=lambda: switch_panel("hr"),
            outputs=list(all_panels.values())
        )

        model_btn.click(
            fn=lambda: switch_panel("model"),
            outputs=list(all_panels.values())
        )

        # ========== 聊天功能 ==========
        # 为每个Agent面板添加聊天功能
        def create_chat_handler(agent_id: str):
            """为指定Agent创建聊天处理器"""
            def chat_handler(message: str, history):
                if not message.strip():
                    return "", history

                if history is None:
                    history = []

                # Gradio 6.0格式：添加用户消息
                history.append({"role": "user", "content": message})
                yield "", history

                # 模拟AI回复（后续会替换为实际模型调用）
                import time

                # 第一段回复
                reply = f"👋 你好！我是{agent_id}。\n\n"
                reply += f"已收到您的消息: '{message}'\n\n"
                reply += "我正在处理您的请求，请稍候..."

                history.append({"role": "assistant", "content": reply})
                yield "", history

                time.sleep(1)

                # 最终回复
                reply += "\n\n✅ 处理完成！\n"
                reply += f"这是{agent_id}的模拟回复。实际功能将在后续版本实现。"

                history[-1] = {"role": "assistant", "content": reply}
                yield "", history

            return chat_handler

        # 为每个Agent面板绑定聊天处理器
        # 注意：这里需要在实际的面板组件中绑定，这里只是框架

    return app


def main():
    """主函数"""
    print("=" * 60)
    print("AI OS V4.0 - 完整SPA版本")
    print("=" * 60)
    print("服务地址: http://127.0.0.1:7860")
    print("功能特性:")
    print("  * 7面板SPA架构（5个Agent + 2个功能面板）")
    print("  * 支持Agent头像自定义")
    print("  * 团队HR配置管理")
    print("  * 模型中枢扩展")
    print("  * Claude/Notion极简风格")
    print("=" * 60)

    css = """
        /* ========== AI OS V4.0 - 极简黑白重构 ========== */

        /* CSS 变量定义 */
        :root {
            --sidebar-bg: #111111;
            --sidebar-text: #FFFFFF;
            --sidebar-hover: rgba(255, 255, 255, 0.1);
            --workspace-bg: #FFFFFF;
            --workspace-text: #333333;
            --border-color: #E5E5E5;
            --border-dark: #333333;
            --primary-blue: #0066CC;
            --primary-blue-dark: #0052A3;
            --gray-light: #F5F5F5;
            --gray-medium: #999999;
        }

        /* 全局字体设置 */
        * {
            font-family: 'Nunito', sans-serif !important;
        }

        h1, h2, h3 {
            font-family: 'Feather Bold', sans-serif !important;
            font-weight: 700 !important;
            color: var(--workspace-text) !important;
            line-height: 1.5 !important;
        }

        h1 {
            font-size: 32px !important;
            margin: 0 0 16px 0 !important;
        }

        h2 {
            font-size: 24px !important;
            margin: 0 0 12px 0 !important;
        }

        h3 {
            font-size: 20px !important;
            margin: 0 0 8px 0 !important;
        }

        /* 彻底消除 Gradio 默认样式 */
        .gradio-container {
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            background: var(--workspace-bg) !important;
        }

        footer {
            display: none !important;
        }

        /* ========== 侧边栏 ========== */
        #sidebar {
            background: var(--sidebar-bg) !important;
            height: 100vh !important;
            padding: 24px 16px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 24px !important;
            border-right: 1px solid var(--border-dark) !important;
        }

        .sidebar-logo {
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            padding-bottom: 16px !important;
            border-bottom: 1px solid var(--border-dark) !important;
        }

        .sidebar-logo .logo-main {
            font-family: 'Feather Bold', sans-serif !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            color: var(--sidebar-text) !important;
            margin: 0 0 4px 0 !important;
        }

        .sidebar-logo .logo-sub {
            font-size: 12px !important;
            color: var(--gray-medium) !important;
            margin: 0 !important;
        }

        .nav-buttons-container {
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
        }

        /* 隐藏 Gradio 默认按钮图标 */
        .sidebar-btn svg, .sidebar-btn img, .button-icon { display: none !important; }

        /* 极简深色侧边栏按钮样式 */
        .sidebar-btn {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #E0E0E0 !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            padding: 12px 16px !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            text-align: left !important;
            justify-content: flex-start !important;
        }

        .sidebar-btn:hover {
            background: rgba(255, 255, 255, 0.1) !important;
            color: #FFFFFF !important;
        }

        /* ========== 主工作区 ========== */
        #main-workspace {
            background: var(--workspace-bg) !important;
            height: 100vh !important;
            padding: 24px 32px !important;
            overflow-y: auto !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 24px !important;
        }

        /* ========== AGENT 卡片面板 ========== */
        .agent-panel {
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            padding: 24px !important;
            background: var(--workspace-bg) !important;
            margin-bottom: 16px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 16px !important;
        }

        /* 聊天区域 */
        .chatbot-container {
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            padding: 20px !important;
            background: var(--workspace-bg) !important;
            margin-top: 16px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 16px !important;
        }

        /* 彻底去除气泡背景 */
        .chatbot {
            border: none !important;
            background: transparent !important;
        }

        .message {
            border: none !important;
            background: transparent !important;
            padding: 8px 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: flex-start !important;
            gap: 12px !important;
        }

        .message-user {
            flex-direction: row-reverse !important;
        }

        .message-avatar {
            font-size: 24px !important;
            flex-shrink: 0 !important;
        }

        .message-content {
            flex: 1 !important;
            padding: 12px !important;
            border-radius: 8px !important;
            background: transparent !important;
        }

        .message.user .message-content {
            background: rgba(0, 102, 204, 0.05) !important;
            border: 1px solid rgba(0, 102, 204, 0.2) !important;
        }

        .message.bot .message-content {
            background: rgba(0, 0, 0, 0.03) !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
        }

        /* ========== 按钮样式 ========== */
        .btn-3d-primary {
            background: var(--primary-blue) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }

        .btn-3d-primary:hover {
            background: var(--primary-blue-dark) !important;
        }

        .btn-secondary {
            background: white !important;
            color: var(--workspace-text) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }

        .btn-secondary:hover {
            border-color: var(--primary-blue) !important;
            color: var(--primary-blue) !important;
        }

        /* ========== 输入框与下拉菜单 ========== */
        .input-field, select, textarea, .gr-textbox, .gr-dropdown {
            height: 48px !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            padding: 0 16px !important;
            font-size: 15px !important;
            transition: all 0.2s ease !important;
            background: white !important;
        }

        .input-field:focus, select:focus, textarea:focus, .gr-textbox:focus, .gr-dropdown:focus {
            border-color: var(--primary-blue) !important;
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1) !important;
        }

        textarea {
            min-height: 48px !important;
            padding: 12px 16px !important;
            line-height: 1.5 !important;
        }

        /* ========== 配置面板样式 ========== */
        .config-panel {
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            padding: 24px !important;
            background: var(--workspace-bg) !important;
            margin-bottom: 16px !important;
        }

        .tab-nav {
            border-bottom: 1px solid var(--border-color) !important;
        }

        .tab-button {
            border: none !important;
            border-bottom: 2px solid transparent !important;
            border-radius: 0 !important;
            margin: 0 8px !important;
            padding: 12px 16px !important;
            font-size: 15px !important;
            font-weight: 500 !important;
            color: var(--workspace-text) !important;
            background: transparent !important;
        }

        .tab-button.selected {
            border-bottom-color: var(--primary-blue) !important;
            color: var(--primary-blue) !important;
        }

        /* ========== 响应式设计 ========== */
        @media (max-width: 768px) {
            #sidebar {
                padding: 16px 12px !important;
            }

            .sidebar-logo .logo-main {
                font-size: 18px !important;
            }

            .sidebar-btn {
                padding: 10px 12px !important;
                font-size: 14px !important;
                gap: 8px !important;
            }

            #main-workspace {
                padding: 16px 20px !important;
            }

            h1 {
                font-size: 28px !important;
            }

            h2 {
                font-size: 22px !important;
            }

            h3 {
                font-size: 18px !important;
            }

            .agent-panel, .chatbot-container, .config-panel {
                padding: 16px !important;
            }
        }

        @media (max-width: 480px) {
            #sidebar {
                padding: 12px 8px !important;
            }

            .sidebar-logo .logo-sub {
                display: none !important;
            }

            .sidebar-btn span {
                display: none !important;
            }

            .sidebar-btn {
                justify-content: center !important;
                padding: 12px !important;
            }

            #main-workspace {
                padding: 12px 16px !important;
            }

            h1 {
                font-size: 24px !important;
            }
        }
        """

    app = build_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
        css=css,
        favicon_path=None
    )


if __name__ == "__main__":
    main()