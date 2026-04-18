# 文件位置：/AI_Auto_System/views/chat_view.py
import os
import ast
import json
import requests
import gradio as gr
from interpreter import interpreter

# 加载 agents 配置
with open("agents_config.json", "r", encoding="utf-8") as f:
    AGENTS_CONFIG = json.load(f)

# 创建 workspace 目录
WORKSPACE_DIR = "./workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "openai/qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
INTERPRETER_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")
INTERPRETER_REQUEST_TIMEOUT = int(os.getenv("INTERPRETER_REQUEST_TIMEOUT", "600"))

DEFAULT_CONTEXT_WINDOW = int(os.getenv("OLLAMA_CONTEXT_WINDOW", "8000"))
DEFAULT_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "1600"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "0").lower() in {"1", "true", "yes"}

# DeepSeek API 配置（假设）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")

MESSAGE_FORMATS = {"message", "markdown"}
CODE_FORMATS = {"code", "python", "bash", "powershell", "sh", "js", "javascript"}
OUTPUT_FORMATS = {"output", "console", "execution"}


def configure_interpreter():
    try:
        interpreter.offline = True
        interpreter.llm.api_base = OLLAMA_HOST
        interpreter.llm.model = OLLAMA_MODEL
        interpreter.llm.api_key = INTERPRETER_API_KEY
        interpreter.llm.context_window = DEFAULT_CONTEXT_WINDOW
        interpreter.llm.max_tokens = DEFAULT_MAX_TOKENS
        if hasattr(interpreter.llm, "request_timeout"):
            interpreter.llm.request_timeout = INTERPRETER_REQUEST_TIMEOUT
        elif hasattr(interpreter.llm, "timeout"):
            interpreter.llm.timeout = INTERPRETER_REQUEST_TIMEOUT
        interpreter.auto_run = True
    except Exception as exc:
        print(f"[WARN] Open Interpreter 初始化失败：{exc}")


configure_interpreter()


def call_deepseek_api(message, system_prompt):
    """调用 DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",  # 假设模型名
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "max_tokens": 1000
    }
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"DeepSeek API 错误: {response.status_code} - {response.text}"


def extract_text(msg):
    """从 Gradio 6.0 的消息格式中提取纯文本。"""
    if isinstance(msg, list):
        texts = []
        for part in msg:
            part_text = extract_text(part)
            if part_text:
                texts.append(part_text)
        return " ".join(texts).strip()

    if isinstance(msg, dict):
        if "text" in msg:
            return str(msg["text"]).strip()
        if "content" in msg:
            return extract_text(msg["content"])
        if "message" in msg:
            return extract_text(msg["message"])
        if "role" in msg and "content" in msg:
            return extract_text(msg["content"])

        texts = []
        for value in msg.values():
            part_text = extract_text(value)
            if part_text:
                texts.append(part_text)
        return " ".join(texts).strip()

    return str(msg).strip()


def normalize_history(chat_history):
    """兼容 Gradio 6.0 历史格式，提取出纯文本的 role/content。"""
    normalized = []
    if not chat_history:
        return normalized

    valid_roles = {"system", "user", "assistant"}
    for item in chat_history:
        try:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                user_part, assistant_part = item
                user_text = extract_text(user_part)
                assistant_text = extract_text(assistant_part)
                if user_text:
                    normalized.append({"role": "user", "content": user_text})
                if assistant_text:
                    normalized.append({"role": "assistant", "content": assistant_text})
                continue

            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content") if "content" in item else item
            else:
                role = getattr(item, "role", None)
                content = getattr(item, "content", item)

            if isinstance(role, str):
                role = role.lower()
                if role == "bot":
                    role = "assistant"
            if role not in valid_roles:
                # 尝试按纯文本保存，避免丢失列表格式输入
                content_text = extract_text(item)
                if content_text:
                    normalized.append({"role": "assistant", "content": content_text})
                continue

            content_text = extract_text(content)
            if content_text:
                normalized.append({"role": role, "content": content_text})
        except Exception:
            continue

    return normalized


def parse_interpreter_chunk(chunk):
    """解析 Open Interpreter chunk 并返回命令/结果/回答三段信息。"""
    if chunk is None:
        return {
            "command": "",
            "output": "",
            "answer": "",
        }

    def decode_possible_json(value):
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("{") or text.startswith("["):
                try:
                    return json.loads(text)
                except Exception:
                    pass
                try:
                    return ast.literal_eval(text)
                except Exception:
                    return value
        return value

    if isinstance(chunk, bytes):
        try:
            chunk = chunk.decode("utf-8", errors="ignore")
        except Exception:
            return {"command": "", "output": "", "answer": ""}

    if isinstance(chunk, str):
        chunk = decode_possible_json(chunk)

    if not isinstance(chunk, dict):
        return {"command": "", "output": "", "answer": str(chunk)}

    # 如果 content 本身是 JSON 字符串，先尝试解析它
    if "content" in chunk:
        parsed_content = chunk["content"]
        if isinstance(parsed_content, str):
            parsed_content = decode_possible_json(parsed_content)
        if isinstance(parsed_content, dict) and ("name" in parsed_content or "tool" in parsed_content):
            return parse_interpreter_chunk(parsed_content)

    if "message" in chunk and isinstance(chunk["message"], dict):
        message_content = chunk["message"].get("content")
        parsed_message = message_content
        if isinstance(parsed_message, str):
            parsed_message = decode_possible_json(parsed_message)
        if isinstance(parsed_message, dict) and ("name" in parsed_message or "tool" in parsed_message):
            return parse_interpreter_chunk(parsed_message)

    command_text = ""
    output_text = ""
    answer_text = ""

    name = chunk.get("name") or chunk.get("tool")
    arguments = chunk.get("arguments") or chunk.get("args") or {}
    if name:
        if name == "execute" and isinstance(arguments, dict):
            language = arguments.get("language", "text")
            code = arguments.get("code")
            if code:
                command_text += f"```{language}\n{code}\n```"
        else:
            command_text += f"工具：{name}\n"
            if isinstance(arguments, dict) and arguments:
                try:
                    command_text += json.dumps(arguments, ensure_ascii=False, indent=2)
                except Exception:
                    command_text += str(arguments)

    if "code" in chunk and chunk["code"] is not None:
        code = str(chunk["code"]).strip()
        if code:
            if command_text:
                command_text += "\n"
            command_text += f"```python\n{code}\n```"

    if "output" in chunk and chunk["output"] is not None:
        output_text = str(chunk["output"]).strip()
        if output_text in ("True", "None"):
            output_text = ""

    content = ""
    if "content" in chunk and chunk["content"] is not None:
        content = str(chunk["content"]).strip()
    if "message" in chunk and isinstance(chunk["message"], dict):
        content += str(chunk["message"].get("content", "")).strip()

    if content and not (content.startswith("{\"name\"") or content.startswith("{ 'name'")):
        if answer_text:
            answer_text += "\n"
        answer_text += content

    return {
        "command": command_text,
        "output": output_text,
        "answer": answer_text,
    }


def render_interpreter_response(command_text, output_text, answer_text):
    parts = []
    if command_text:
        parts.append(
            "> **执行命令：**\n" + command_text.strip()
        )
    if output_text:
        parts.append(
            "> **执行结果：**\n> " + output_text.replace("\n", "\n> ").strip()
        )
    if answer_text:
        parts.append(
            "> **最终回答：**\n" + answer_text.strip()
        )
    return "\n\n".join(parts) + ("\n" if parts else "")


def chief_agent_chat(user_message, history):
    """调用 Open Interpreter 进行自动执行，并流式返回助手输出。"""

    processed_user_message = extract_text(user_message)
    cleaned_history = normalize_history(history)

    try:
        chunks = interpreter.chat(processed_user_message, stream=True, display=False)
        full_response = ""
        has_content = False
        inside_code_block = False

        for chunk in chunks:
            if DEBUG_MODE:
                print(f"DEBUG CHUNK: {chunk}")
            has_content = True
            if not isinstance(chunk, dict):
                continue

            chunk_type = str(chunk.get("type", "")).lower()
            chunk_format = str(chunk.get("format", "")).lower()
            is_message = chunk_format in MESSAGE_FORMATS or chunk_type == "message"
            is_code = chunk_format in CODE_FORMATS or chunk_type == "code"
            is_output = chunk_format in OUTPUT_FORMATS or chunk_type in OUTPUT_FORMATS

            if is_message:
                message_text = extract_text(chunk.get("message", chunk.get("content", "")))
                if message_text and message_text.strip().lower() != "markdown":
                    if inside_code_block:
                        if not full_response.endswith("```\n"):
                            full_response += "\n```\n"
                        inside_code_block = False
                    full_response += message_text

            elif is_code:
                code_text = extract_text(chunk.get("code", chunk.get("content", "")))
                if code_text:
                    if not inside_code_block:
                        if full_response and not full_response.endswith("\n"):
                            full_response += "\n"
                        full_response += f"\n\n```python\n{code_text}"
                    else:
                        full_response += code_text
                    inside_code_block = True

            elif is_output:
                output_text = extract_text(chunk.get("output", chunk.get("content", "")))
                if output_text and output_text not in ("True", "None"):
                    if inside_code_block:
                        if not full_response.endswith("```\n"):
                            full_response += "\n```\n"
                        inside_code_block = False
                    full_response += f"\n\n> **运行结果:**\n> {output_text}\n"

            if full_response:
                yield full_response

        if inside_code_block and not full_response.endswith("```\n"):
            full_response += "\n```\n"
            yield full_response

        if not has_content:
            yield "⚠️ 大脑连接成功但未产生有效输出，请尝试换个问题或检查 Ollama 负载。"
    except Exception as e:
        yield f"⚠️ 核心引擎报错: {str(e)}"


def handle_user_input(user_msg, chat_history):
    """处理用户输入，调用 Open Interpreter 并在 Chatbot 中流式输出。"""
    if chat_history is None:
        chat_history = []
    else:
        chat_history = normalize_history(chat_history)

    chat_history.append({"role": "user", "content": user_msg})
    assistant_message = {"role": "assistant", "content": ""}
    chat_history.append(assistant_message)

    for partial_output in chief_agent_chat(user_msg, chat_history):
        assistant_message["content"] = partial_output
        yield "", chat_history

def render_chat_view():
    """渲染聊天总控台的独立组件"""
    with gr.Column(scale=1):
        # 对话展示区
        chatbot = gr.Chatbot(
            height="70vh",          # 适配屏幕高度
            show_label=False,
            buttons=["copy", "copy_all"],  # 实用工具，兼容当前 Gradio 版本
        )
        
        # 用户输入区 (绑定自定义 ID 以应用软阴影 CSS)
        with gr.Group(elem_id="input-group"):
            with gr.Row(equal_height=True):
                msg_input = gr.Textbox(
                    show_label=False,
                    placeholder="给 AI 助手发送指令... (Shift + Enter 换行)",
                    lines=1,
                    max_lines=8,    # 文本框自适应增长
                    container=False,
                    scale=8
                )
                submit_btn = gr.Button("发送", variant="primary", scale=1, min_width=80)

        # 核心事件绑定
        msg_input.submit(
            handle_user_input, 
            inputs=[msg_input, chatbot], 
            outputs=[msg_input, chatbot]
        )
        submit_btn.click(
            handle_user_input, 
            inputs=[msg_input, chatbot], 
            outputs=[msg_input, chatbot]
        )