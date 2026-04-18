"""
Plobi - Liquid Glass Dashboard
Modern liquid glass UI for AI agent system
"""

import json
import os
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 强制绕过系统代理，解决 502 Bad Gateway 问题
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
# 禁用 Gradio 分析，避免网络请求失败
os.environ["GRADIO_ANALYTICS_ENABLED"] = "0"

import gradio as gr
from core.llm_engine import get_llm_engine
from core.tools.audio_analyzer import analyze_audio_track
from core.session_manager import save_session, list_sessions, load_session

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


def create_hero_section() -> gr.HTML:
    """创建液态玻璃风格英雄区域"""
    hero_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Plobi - Liquid Glass Interface</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fustat:wght@700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }

            .hero-container {
                font-family: 'Inter', sans-serif;
                background: #FFFFFF;
                color: #000000;
                min-height: 100vh;
                position: relative;
                overflow: hidden;
            }

            /* Background gradient glow */
            .bg-glow {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                z-index: 0;
                pointer-events: none;
            }

            .glow-ellipse-1 {
                position: absolute;
                top: -200px;
                left: -200px;
                width: 800px;
                height: 800px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(96, 177, 255, 0.3) 0%, rgba(49, 154, 255, 0.1) 50%, transparent 70%);
                filter: blur(80px);
                opacity: 0.6;
            }

            .glow-ellipse-2 {
                position: absolute;
                top: -150px;
                left: -150px;
                width: 600px;
                height: 600px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(96, 177, 255, 0.4) 0%, rgba(49, 154, 255, 0.2) 50%, transparent 70%);
                filter: blur(60px);
                opacity: 0.4;
            }

            /* Main content */
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 80px 32px;
                position: relative;
                z-index: 10;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                gap: 48px;
            }

            /* Logo and header */
            .header {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 16px;
            }

            .logo {
                font-family: 'Fustat', sans-serif;
                font-size: 48px;
                font-weight: 700;
                color: #000000;
                text-decoration: none;
            }

            .tagline {
                font-size: 18px;
                color: #666666;
                letter-spacing: -0.5px;
                max-width: 600px;
                line-height: 1.6;
            }

            /* Hero headline */
            .hero-headline {
                font-family: 'Fustat', sans-serif;
                font-size: 64px;
                font-weight: 700;
                line-height: 1.05;
                letter-spacing: -2px;
                color: #000000;
                max-width: 800px;
            }

            @media (max-width: 768px) {
                .hero-headline {
                    font-size: 48px;
                }

                .logo {
                    font-size: 36px;
                }
            }

            /* Subheadline */
            .hero-subheadline {
                font-family: 'Inter', sans-serif;
                font-size: 20px;
                line-height: 1.6;
                letter-spacing: -1px;
                color: #666666;
                max-width: 600px;
            }

            /* CTA Buttons */
            .cta-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: center;
                margin-top: 24px;
            }

            .primary-cta {
                display: inline-flex;
                align-items: center;
                gap: 12px;
                background: rgba(0, 132, 255, 0.8);
                backdrop-filter: blur(2px);
                border: none;
                border-radius: 16px;
                padding: 18px 32px;
                font-family: 'Inter', sans-serif;
                font-size: 16px;
                font-weight: 500;
                color: #FFFFFF;
                text-decoration: none;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                cursor: pointer;
                box-shadow:
                    inset 0px 4px 4px 0px rgba(255, 255, 255, 0.35),
                    0px 8px 32px rgba(0, 132, 255, 0.2);
            }

            .primary-cta:hover {
                transform: scale(1.02);
                background: rgba(0, 132, 255, 0.9);
                box-shadow:
                    inset 0px 4px 4px 0px rgba(255, 255, 255, 0.4),
                    0px 12px 40px rgba(0, 132, 255, 0.3);
            }

            .secondary-cta {
                display: inline-flex;
                align-items: center;
                gap: 12px;
                background: rgba(255, 255, 255, 0.4);
                backdrop-filter: blur(4px);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 16px;
                padding: 18px 32px;
                font-family: 'Inter', sans-serif;
                font-size: 16px;
                font-weight: 500;
                color: #000000;
                text-decoration: none;
                transition: all 0.3s ease;
                cursor: pointer;
                box-shadow:
                    inset 0px 4px 4px rgba(255, 255, 255, 0.3),
                    0px 2px 8px rgba(0, 0, 0, 0.1);
            }

            .secondary-cta:hover {
                background: rgba(255, 255, 255, 0.6);
                transform: translateY(-1px);
                box-shadow:
                    inset 0px 4px 4px rgba(255, 255, 255, 0.4),
                    0px 4px 16px rgba(0, 0, 0, 0.15);
            }

            .cta-arrow {
                font-size: 20px;
                transition: transform 0.3s ease;
            }

            .primary-cta:hover .cta-arrow,
            .secondary-cta:hover .cta-arrow {
                transform: translateX(4px);
            }

            /* Feature cards */
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 24px;
                margin-top: 60px;
                width: 100%;
            }

            .feature-card {
                background: rgba(255, 255, 255, 0.6);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 20px;
                padding: 32px;
                text-align: left;
                transition: all 0.3s ease;
            }

            .feature-card:hover {
                transform: translateY(-4px);
                background: rgba(255, 255, 255, 0.8);
                box-shadow: 0px 12px 32px rgba(0, 0, 0, 0.1);
            }

            .feature-icon {
                font-size: 32px;
                margin-bottom: 16px;
            }

            .feature-title {
                font-family: 'Fustat', sans-serif;
                font-size: 20px;
                font-weight: 700;
                color: #000000;
                margin-bottom: 12px;
            }

            .feature-description {
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #666666;
            }

            /* Social proof */
            .social-proof {
                display: inline-flex;
                align-items: center;
                gap: 12px;
                background: rgba(255, 255, 255, 0.6);
                backdrop-filter: blur(8px);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 100px;
                padding: 12px 24px;
                margin-top: 40px;
            }

            .stars {
                display: flex;
                gap: 2px;
            }

            .star {
                color: #FF801E;
                font-size: 16px;
            }

            .rating-text {
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 500;
                color: #000000;
            }
        </style>
    </head>
    <body>
        <div class="hero-container">
            <div class="bg-glow">
                <div class="glow-ellipse-1"></div>
                <div class="glow-ellipse-2"></div>
            </div>

            <div class="container">
                <div class="header">
                    <div class="logo">Plobi</div>
                    <p class="tagline">Next-generation AI operating system - Liquid glass interface</p>
                </div>

                <h1 class="hero-headline">Work smarter, achieve faster</h1>

                <p class="hero-subheadline">
                    A modern operating system integrating multiple AI agents, helping you efficiently manage projects, automate tasks, and accelerate workflows.
                </p>

                <div class="social-proof">
                    <div class="stars">
                        <span class="star">★</span>
                        <span class="star">★</span>
                        <span class="star">★</span>
                        <span class="star">★</span>
                        <span class="star">★</span>
                    </div>
                    <span class="rating-text">Rated 4.9/5 by 2700+ customers</span>
                </div>

                <div class="cta-container">
                    <button class="primary-cta" id="launch-os-btn">
                        Launch Plobi
                        <span class="cta-arrow">→</span>
                    </button>
                    <button class="secondary-cta" id="view-demo-btn">
                        View Demo
                        <span class="cta-arrow">→</span>
                    </button>
                </div>

                <div class="features">
                    <div class="feature-card">
                        <div class="feature-icon">👩‍💼</div>
                        <h3 class="feature-title">AI Assistant</h3>
                        <p class="feature-description">
                            Intelligent project manager assistant, helping you analyze requirements, break down tasks, and generate detailed task documentation.
                        </p>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">💻</div>
                        <h3 class="feature-title">Automation Expert</h3>
                        <p class="feature-description">
                            自动化专家，执行Python脚本和系统操作，将任务转化为实际行动。
                        </p>
                    </div>

                    <div class="feature-card">
                        <div class="feature-icon">🎨</div>
                        <h3 class="feature-title">System Architect</h3>
                        <p class="feature-description">
                            系统架构师，设计复杂系统架构，提供技术选型和架构图设计。
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const launchBtn = document.getElementById('launch-os-btn');
                const demoBtn = document.getElementById('view-demo-btn');

                if (launchBtn) {
                    launchBtn.addEventListener('click', function() {
                        // 这里可以触发Gradio事件切换到AI OS工作区
                        window.parent.postMessage({ type: 'SWITCH_TO_OS' }, '*');
                    });
                }

                if (demoBtn) {
                    demoBtn.addEventListener('click', function() {
                        alert('Demo feature coming soon!');
                    });
                }
            });
        </script>
    </body>
    </html>
    """
    return gr.HTML(hero_html)


def create_top_navbar() -> Tuple[gr.Button, gr.Button, gr.Button, gr.Button]:
    """Create ultra-compact top navigation bar for desktop (1000x700 window)
    Returns: home_btn, settings_btn, models_btn, agents_btn
    """
    with gr.Row(elem_id="top-nav", elem_classes=["top-navbar", "compact-navbar"]):
        # Left side: Project name "Plobi"
        gr.HTML("""
        <div class="navbar-logo">
            <span class="logo-text">Plobi</span>
        </div>
        """)

        # Right side: All navigation buttons in a single row
        with gr.Row(elem_classes="navbar-buttons"):
            home_btn = gr.Button("⌂ Home", variant="primary", elem_classes="nav-btn", size="sm")
            settings_btn = gr.Button("⚙ Settings", variant="secondary", elem_classes="nav-btn", size="sm")
            models_btn = gr.Button("🖥 Models", variant="secondary", elem_classes="nav-btn", size="sm")
            agents_btn = gr.Button("👤 Agents", variant="secondary", elem_classes="nav-btn", size="sm")

    return home_btn, settings_btn, models_btn, agents_btn


def create_home_panel(agents_config: Dict[str, Any], models_config: Dict[str, Any]) -> Tuple[gr.Column, gr.MultimodalTextbox, List[gr.Button], List[str]]:
    """Create Gemini-style minimalist home panel for desktop (1000x700 window)
    Args:
        agents_config: Agents configuration dictionary
        models_config: Models configuration dictionary
    Returns:
        Tuple of (panel, home_input, card_buttons, agent_ids) - card_buttons and agent_ids are now populated with specialist cards
    """
    with gr.Column(elem_classes="home-panel") as panel:
        # Store card button references for external connection
        card_buttons = []
        agent_ids = []

        # Centered Gemini input with max-width 750px and margin-top 25vh
        with gr.Row():
            with gr.Column(scale=1):
                pass  # Left spacer
            with gr.Column(scale=8, elem_classes="gemini-input-wrapper"):
                home_input = gr.MultimodalTextbox(
                    placeholder="Describe your task or ask a question...",
                    show_label=False,
                    elem_classes=["glass-input"]
                )
            with gr.Column(scale=1):
                pass  # Right spacer

        # Specialist cards row (horizontal, compact) - 40px below input
        with gr.Row(elem_classes="specialist-cards-row"):
            # Define specialist agents (excluding assistant)
            specialist_agents = []
            for agent in agents_config.get("agents", []):
                agent_id = agent.get("id", "")
                if agent_id in ["geek", "architect", "publisher", "scout"] and agent.get("active", True):
                    specialist_agents.append({
                        "id": agent_id,
                        "name": agent.get("name", agent_id.title()),
                        "icon": DEFAULT_AVATARS.get(agent_id, "🤖"),
                        "role": agent.get("role", "")
                    })

            # Create cards for each specialist
            for spec in specialist_agents:
                with gr.Column(scale=1, min_width=100):
                    card_btn = gr.Button(
                        value=f"{spec['icon']} {spec['name']}",
                        elem_classes=["agent-card"],
                        variant="secondary",
                        size="sm"
                    )
                    # Store button and agent ID for external event binding
                    card_buttons.append(card_btn)
                    agent_ids.append(spec['id'])

        # Add CSS for positioning and spacing
        gr.HTML("""
        <style>
        .gemini-input-wrapper {
            max-width: 750px !important;
            margin: calc(25vh + 50px) auto 0 auto !important;
        }
        .specialist-cards-row {
            justify-content: center !important;
            margin-top: 40px !important;
            gap: 16px !important;
            flex-wrap: wrap !important;
        }
        </style>
        """)

    return panel, home_input, card_buttons, agent_ids

def create_models_panel(models_config: Dict[str, Any], visible: bool = False) -> gr.Column:
    """Create models configuration panel with minimalist card layout"""
    from pathlib import Path
    import json

    config_path = CONFIG_DIR / "models_config.json"

    with gr.Column(elem_classes="glass-agent-panel", visible=visible) as panel:
        # Top toolbar with title and Add Model button
        with gr.Row():
            gr.HTML("<h2 style='font-family: \"Fustat\", sans-serif; margin-bottom: 0;'>Model Management</h2>")
            add_model_btn = gr.Button("➕ Add Model", variant="primary", elem_classes="glass-btn", scale=0, min_width=120)

        gr.Markdown("Configure your AI model connections below. Each card represents a model configuration.")

        # Hidden form for adding/editing models
        with gr.Column(visible=False, elem_classes=["model-form"]) as model_form:
            gr.Markdown("### Add/Edit Model")
            model_name_input = gr.Textbox(label="Model Name", placeholder="e.g., DeepSeek")
            model_id_input = gr.Textbox(label="Model ID", placeholder="e.g., deepseek")
            model_desc_input = gr.Textbox(label="Description (optional)", placeholder="Description of the model")
            api_key_input = gr.Textbox(label="API Key", type="password", placeholder="Your API key")
            api_base_input = gr.Textbox(label="API Base URL", placeholder="https://api.deepseek.com/v1")
            active_checkbox = gr.Checkbox(label="Active", value=True)

            with gr.Row():
                save_model_btn = gr.Button("💾 Save Model", variant="primary", elem_classes="glass-btn")
                cancel_btn = gr.Button("Cancel", variant="secondary", elem_classes="glass-btn")

        models = models_config.get("models", [])
        model_ids = []
        active_checkboxes = []
        edit_buttons = []
        delete_buttons = []

        # Store mapping from model_id to index for editing
        model_index_map = {}

        for idx, model in enumerate(models):
            model_id = model.get("id", "")
            model_name = model.get("name", "")
            model_desc = model.get("description", "")
            active = model.get("active", False)
            api_key = model.get("api_key", "")
            api_base = model.get("api_base", "")

            with gr.Row(elem_classes=["sleek-model-card"]):
                # Left side: Model info with active toggle (scale=7)
                with gr.Column(scale=7):
                    with gr.Row():
                        active_cb = gr.Checkbox(value=active, label="", scale=0, elem_classes="model-active-checkbox")
                        gr.HTML(f'''
                        <div style='line-height:1.2; padding:8px 0;'>
                            <b style='font-size:15px;'>{model_name}</b>
                            <span style='font-size:13px; color:#6B7280;'> ({model_id})</span><br>
                            <span style='font-size:12px; color:gray;'>{api_base if api_base else "No base URL"}</span>
                        </div>
                        ''', scale=1)
                # Right side: Action buttons (scale=3)
                with gr.Column(scale=3):
                    with gr.Row():
                        edit_btn = gr.Button("Edit", scale=1, min_width=60, size="sm", variant="secondary", elem_classes="model-action-btn")
                        delete_btn = gr.Button("Delete", scale=1, min_width=60, size="sm", variant="secondary", elem_classes="model-action-btn")

            model_ids.append(model_id)
            active_checkboxes.append(active_cb)
            edit_buttons.append(edit_btn)
            delete_buttons.append(delete_btn)
            model_index_map[model_id] = idx

        gr.HTML("<hr style='margin: 30px 0;'>")
        gr.Markdown("### Agent Model Mappings")

        model_mappings = models_config.get("model_mappings", {})
        mapping_dropdowns = []
        with gr.Row():
            for agent_id, current_model_id in model_mappings.items():
                # Only include active models in dropdown
                active_model_ids = [m["id"] for m in models if m.get("active", False)]
                dropdown = gr.Dropdown(
                    choices=active_model_ids,
                    value=current_model_id if current_model_id in active_model_ids else active_model_ids[0] if active_model_ids else "",
                    label=f"{agent_id.capitalize()} Agent",
                    scale=1
                )
                mapping_dropdowns.append(dropdown)

        save_btn = gr.Button("💾 Save Configuration", variant="primary", elem_classes="glass-btn")
        status_text = gr.Textbox(label="Status", interactive=False, visible=False)

        # Function to show add model form
        def show_add_form():
            return gr.update(visible=True), "", "", "", "", "", True

        # Function to show edit form for a specific model
        def show_edit_form(model_id):
            idx = model_index_map.get(model_id)
            if idx is None:
                return gr.update(visible=False), "", "", "", "", "", False
            model = models[idx]
            return (
                gr.update(visible=True),
                model.get("name", ""),
                model.get("id", ""),
                model.get("description", ""),
                model.get("api_key", ""),
                model.get("api_base", ""),
                model.get("active", False)
            )

        # Function to save model (add new or update existing)
        def save_model(model_name, model_id, description, api_key, api_base, active):
            try:
                # Load current config
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                else:
                    config = {"models": [], "model_mappings": {}}

                # Check if model_id already exists
                existing_idx = -1
                existing_model = None
                for i, m in enumerate(config["models"]):
                    if m["id"] == model_id:
                        existing_idx = i
                        existing_model = m
                        break

                # Prepare updated fields
                updated_fields = {
                    "id": model_id,
                    "name": model_name,
                    "description": description,
                    "api_key": api_key,
                    "api_base": api_base,
                    "active": active
                }

                # Determine type and provider if new model
                if existing_idx >= 0:
                    # Update existing model - preserve other fields
                    model_data = existing_model.copy()
                    model_data.update(updated_fields)
                    # Ensure type is set correctly based on API key
                    model_data["type"] = "cloud" if api_key else "local"
                    # Keep existing provider if present
                    if "provider" not in model_data:
                        model_data["provider"] = model_id.split("_")[0] if "_" in model_id else model_id
                    message = f"Model '{model_name}' updated successfully!"
                else:
                    # Create new model with sensible defaults
                    model_data = {
                        "type": "cloud" if api_key else "local",
                        "provider": model_id.split("_")[0] if "_" in model_id else model_id,
                        "default_model": model_id,
                        "context_window": 32000,
                        "max_tokens": 2000,
                        "timeout": 120,
                        **updated_fields
                    }
                    message = f"Model '{model_name}' added successfully!"

                if existing_idx >= 0:
                    config["models"][existing_idx] = model_data
                else:
                    config["models"].append(model_data)

                # Save to file
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                print(f"✅ Model configuration saved to: {config_path}")

                # Reload LLM engine configurations to pick up the changes
                try:
                    llm_engine = get_llm_engine()
                    llm_engine.reload_configs()
                    print(f"🔄 Reloaded LLM engine configurations")
                except Exception as engine_error:
                    print(f"⚠️ Failed to reload LLM engine: {engine_error}")

                gr.Info(message)
                return gr.update(visible=False), message
            except Exception as e:
                error_msg = f"Error saving model: {str(e)}"
                gr.Error(error_msg)
                return gr.update(visible=True), error_msg

        # Function to delete a model
        def delete_model(model_id):
            try:
                if not config_path.exists():
                    # Nothing to delete
                    return f"No configuration file found. Nothing to delete."

                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Remove model from list
                new_models = [m for m in config["models"] if m["id"] != model_id]

                # Check if model was actually removed
                if len(new_models) == len(config["models"]):
                    return f"Model '{model_id}' not found in configuration."

                config["models"] = new_models

                # Save to file
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                print(f"🗑️ Model '{model_id}' deleted from: {config_path}")

                # Reload LLM engine configurations to pick up the changes
                try:
                    llm_engine = get_llm_engine()
                    llm_engine.reload_configs()
                    print(f"🔄 Reloaded LLM engine configurations after deletion")
                except Exception as engine_error:
                    print(f"⚠️ Failed to reload LLM engine: {engine_error}")

                gr.Info(f"Model '{model_id}' deleted successfully!")
                return f"Model '{model_id}' deleted. Please refresh the page to see changes."
            except Exception as e:
                error_msg = f"Error deleting model: {str(e)}"
                gr.Error(error_msg)
                return error_msg

        def save_configuration(*args):
            try:
                # Calculate offsets
                n = len(model_ids)
                active_vals = args[:n]
                mapping_vals = args[n:]

                # Load current config to preserve other fields
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Update active status for each model
                for i, model_id in enumerate(model_ids):
                    for model in config["models"]:
                        if model["id"] == model_id:
                            model["active"] = active_vals[i]
                            break

                # Update model_mappings
                new_mappings = {}
                for j, agent_id in enumerate(model_mappings.keys()):
                    new_mappings[agent_id] = mapping_vals[j]
                config["model_mappings"] = new_mappings

                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                print(f"💾 Full configuration saved to: {config_path}")

                # Reload LLM engine configurations to pick up the changes
                try:
                    llm_engine = get_llm_engine()
                    llm_engine.reload_configs()
                    print(f"🔄 Reloaded LLM engine configurations after full save")
                except Exception as engine_error:
                    print(f"⚠️ Failed to reload LLM engine: {engine_error}")

                # Show success notification
                gr.Info("Configuration saved successfully!")
                return "✅ Configuration saved successfully!"
            except Exception as e:
                # Show error notification
                gr.Error(f"Error saving configuration: {str(e)}")
                return f"❌ Error saving configuration: {str(e)}"

        # Connect Add Model button
        add_model_btn.click(
            fn=show_add_form,
            inputs=None,
            outputs=[model_form, model_name_input, model_id_input, model_desc_input, api_key_input, api_base_input, active_checkbox]
        )

        # Connect Edit buttons
        for i, edit_btn in enumerate(edit_buttons):
            edit_btn.click(
                fn=lambda idx=i: show_edit_form(model_ids[idx]),
                inputs=None,
                outputs=[model_form, model_name_input, model_id_input, model_desc_input, api_key_input, api_base_input, active_checkbox]
            )

        # Connect Save Model button
        save_model_btn.click(
            fn=save_model,
            inputs=[model_name_input, model_id_input, model_desc_input, api_key_input, api_base_input, active_checkbox],
            outputs=[model_form, status_text]
        )

        # Connect Cancel button
        cancel_btn.click(
            fn=lambda: gr.update(visible=False),
            inputs=None,
            outputs=[model_form]
        )

        # Connect Delete buttons
        for i, delete_btn in enumerate(delete_buttons):
            delete_btn.click(
                fn=lambda idx=i: delete_model(model_ids[idx]),
                inputs=None,
                outputs=[status_text]
            )

        # Connect Save Configuration button
        all_inputs = active_checkboxes + mapping_dropdowns
        save_btn.click(save_configuration, inputs=all_inputs, outputs=[status_text])

    return panel


def create_settings_panel(visible: bool = False) -> gr.Column:
    """Create system settings panel with working theme toggle"""
    from pathlib import Path
    import json

    config_path = CONFIG_DIR / "settings.json"

    with gr.Column(elem_classes="glass-agent-panel", visible=visible) as panel:
        gr.HTML("<h2 style='font-family: \"Fustat\", sans-serif; margin-bottom: 20px;'>System Settings</h2>")

        # Theme toggle button with JavaScript binding
        gr.Markdown("### Theme")

        # Theme selection radio (for persistent setting)
        theme_radio = gr.Radio(
            choices=["Light", "Dark"],
            value="Light",
            label="UI Theme Preference",
            info="Select theme (applied immediately)"
        )
        theme_radio.change(
            fn=None,
            inputs=[theme_radio],
            outputs=None,
            js="(choice) => { if (choice === 'Dark') { document.body.classList.add('dark'); if (window.gradio_config) window.gradio_config.theme = 'dark'; } else { document.body.classList.remove('dark'); if (window.gradio_config) window.gradio_config.theme = 'light'; } }"
        )

        # Workspace path
        workspace_path = gr.Textbox(
            label="Workspace Directory",
            value=str(Path(__file__).resolve().parent.parent / "workspace"),
            placeholder="Path to workspace directory"
        )

        # Save settings button
        save_btn = gr.Button("💾 Save Settings", variant="primary", elem_classes="glass-btn")
        status_text = gr.Textbox(label="Status", interactive=False, visible=False)

        def save_settings(theme: str, workspace: str):
            try:
                settings = {
                    "theme": theme,
                    "workspace_path": workspace
                }
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)

                # Apply theme immediately
                if theme == "Dark":
                    gr.Info("Settings saved! Applied dark theme.")
                else:  # Light
                    gr.Info("Settings saved! Applied light theme.")

                return f"✅ Settings saved: Theme={theme}, Workspace={workspace}"
            except Exception as e:
                gr.Error(f"Error saving settings: {str(e)}")
                return f"❌ Error saving settings: {str(e)}"

        save_btn.click(save_settings, inputs=[theme_radio, workspace_path], outputs=[status_text])

    return panel


def create_simple_agent_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False) -> gr.Column:
    """创建简化版Agent面板（用于演示）"""
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")

    with gr.Column(elem_classes="glass-agent-panel", visible=visible) as panel:
        # 面板标题
        gr.HTML(f"""
        <div class="glass-panel-header">
            <div class="agent-avatar">{DEFAULT_AVATARS.get(agent_id, "🤖")}</div>
            <div class="agent-info">
                <h3 class="agent-name">{agent_name}</h3>
                <p class="agent-role">{agent_role}</p>
            </div>
        </div>
        """)

        # 聊天区域
        chatbot = gr.Chatbot(
            label="",
            height=300,
            show_label=False,
            render_markdown=True,
            elem_classes="glass-chatbot"
        )

        # 输入区域
        with gr.Row():
            msg_input = gr.Textbox(
                placeholder=f"Message {agent_name}...",
                lines=1,
                max_lines=3,
                container=False,
                scale=9,
                elem_classes="glass-input"
            )
            send_btn = gr.Button("Send", variant="secondary", scale=1, min_width=80, elem_classes="glass-btn")

        # 简单聊天处理
        def chat_handler(message: str, history):
            if not message.strip():
                return "", history

            if history is None:
                history = []

            history.append({"role": "user", "content": message})
            yield "", history

            # 模拟回复
            import time
            reply = f"👋 Hello! I'm {agent_name} ({agent_role}).\n\nI received your message: '{message}'\n\nThis is a demo response in the liquid glass interface."

            history.append({"role": "assistant", "content": reply})
            yield "", history

        # 绑定事件
        msg_input.submit(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        send_btn.click(chat_handler, [msg_input, chatbot], [msg_input, chatbot])

    return panel


def create_glass_assistant_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False, on_home_click=None) -> Tuple[gr.Column, gr.Button, gr.Chatbot, gr.Textbox, gr.Button, gr.State]:
    """创建液态玻璃风格助理面板
    Args:
        agent: Agent configuration dictionary
        models_config: Models configuration dictionary
        visible: Whether panel is visible initially
        on_home_click: Optional callback for home button click
    """
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")
    personality = agent.get("personality", "")
    system_prompt = agent.get("system_prompt", "")
    skills = agent.get("skills", [])

    with gr.Column(elem_classes="glass-agent-panel", visible=visible) as panel:
        # 面板标题
        gr.HTML(f"""
        <div class="glass-panel-header">
            <div class="agent-avatar">{DEFAULT_AVATARS.get(agent_id, "🤖")}</div>
            <div class="agent-info">
                <h3 class="agent-name">{agent_name}</h3>
                <p class="agent-role">{agent_role}</p>
            </div>
        </div>
        """)

        # Home button to return to main dashboard
        with gr.Row():
            home_btn = gr.Button("← Back to Home", variant="secondary", elem_classes="nav-btn", size="sm")
            if on_home_click:
                home_btn.click(fn=on_home_click, inputs=None, outputs=None)

        # 个性描述
        gr.Markdown(f"**Personality**: {personality}")

        # 技能栈
        if skills:
            skills_text = " | ".join(skills)
            gr.Markdown(f"**Skills**: {skills_text}")

        # 系统提示词预览
        with gr.Accordion("System Prompt", open=False):
            gr.Markdown(f"```\n{system_prompt}\n```")

        # 分隔线
        gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);'>")

        # 聊天区域与会话历史 (两栏布局)
        with gr.Row():
            # 左侧：聊天界面 (scale 3)
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="",
                    height=400,
                    show_label=False,
                    render_markdown=True,
                    elem_classes="glass-chatbot"
                )

                # 输入区域
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder=f"Chat with {agent_name}... (Press Enter to send)",
                        lines=2,
                        max_lines=6,
                        container=False,
                        scale=9,
                        elem_classes="glass-input"
                    )
                    send_btn = gr.Button("Send", variant="secondary", scale=1, min_width=80, elem_classes="glass-btn")

                # 功能按钮
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", variant="secondary", elem_classes="glass-btn")
                    export_btn = gr.Button("Export Chat", variant="secondary", elem_classes="glass-btn")
                    task_btn = gr.Button("Generate Task", variant="primary", elem_classes="glass-btn")

            # 右侧：会话历史 (scale 1)
            with gr.Column(scale=1):
                gr.HTML("""
                <div class="session-history-header">
                    <h3 style="margin-top: 0; font-size: 16px; font-weight: 600; color: #000;">Session History</h3>
                    <p style="font-size: 12px; color: #666; margin-top: 4px;">Recent conversations</p>
                </div>
                """)

                # 新建聊天按钮
                new_chat_btn = gr.Button("＋ New Chat", variant="primary", elem_classes="glass-btn", size="sm")

                # 动态会话历史列表
                session_list = gr.Column()

                # 刷新按钮
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm", elem_classes="glass-btn")

        # 会话状态（隐藏）
        current_session_id = gr.State(value="")

        # 会话历史CSS
        gr.HTML("""
        <style>
        .session-history-header {
            border-bottom: 1px solid rgba(0,0,0,0.1);
            padding-bottom: 12px;
            margin-bottom: 16px;
        }
        .session-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .session-item {
            background: rgba(255,255,255,0.6);
            border-radius: 8px;
            padding: 12px;
            border: 1px solid rgba(0,0,0,0.08);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .session-item:hover {
            background: rgba(255,255,255,0.9);
            border-color: rgba(0,132,255,0.3);
            transform: translateY(-1px);
        }
        .session-title {
            font-size: 14px;
            font-weight: 500;
            color: #000;
            margin-bottom: 4px;
        }
        .session-time {
            font-size: 12px;
            color: #666;
        }
        </style>
        """)

        # 更新侧边栏函数
        def update_sidebar():
            sessions = list_sessions()
            session_buttons = []
            for session in sessions[:10]:  # 最多显示10个最近会话
                btn = gr.Button(
                    f"{session['title']}\n{session['time'][:10]}", 
                    variant="secondary", 
                    elem_classes="session-item"
                )
                session_buttons.append(btn)
            return session_buttons

        # 加载会话函数
        def load_selected_session(session_id, current_id):
            if session_id == current_id:
                return gr.update(), current_id
            
            history = load_session(session_id)
            return history, session_id

        # 创建新聊天函数
        def create_new_chat():
            return [], ""

        # 聊天事件处理（带自动保存）
        def chat_handler(message: str, history, session_id):
            if not message.strip():
                return "", history, session_id

            if history is None:
                history = []

            # Gradio 6.0格式：添加用户消息
            history.append({"role": "user", "content": message})
            yield "", history, session_id

            try:
                # 初始化LLM引擎
                llm_engine = get_llm_engine()

                # 临时添加一个初始回复，让用户知道正在处理
                initial_reply = f"👋 Hello! I'm {agent_name} ({agent_role}).\n\n"
                initial_reply += f"Received your message: '{message}'\n\n"
                initial_reply += f"Based on my personality ({personality}), I'm processing your request..."

                history.append({"role": "assistant", "content": initial_reply})
                yield "", history, session_id

                # 使用LLM引擎生成流式响应
                full_response = ""
                for chunk in llm_engine.generate_stream(agent_id, message, history[:-1]):  # 排除刚添加的初始回复
                    full_response += chunk
                    # 更新最后一条消息的内容
                    history[-1] = {"role": "assistant", "content": initial_reply + full_response}
                    yield "", history, session_id

                # 对话完成后自动保存会话
                new_session_id = save_session(session_id, history)
                yield "", history, new_session_id

            except Exception as e:
                # Error handling: Return friendly error message
                error_msg = f"❌ Sorry, an error occurred while processing your request:\n\n```\n{str(e)}\n```\n\n"
                error_msg += "Please check:\n1. Model configuration is correct\n2. API key is valid\n3. Network connection is normal"

                if history and len(history) > 0 and history[-1].get("role") == "assistant":
                    history[-1] = {"role": "assistant", "content": error_msg}
                else:
                    history.append({"role": "assistant", "content": error_msg})
                yield "", history, session_id

        # 绑定聊天事件
        msg_input.submit(chat_handler, [msg_input, chatbot, current_session_id], [msg_input, chatbot, current_session_id])
        send_btn.click(chat_handler, [msg_input, chatbot, current_session_id], [msg_input, chatbot, current_session_id])

        # Clear Chat按钮
        def clear_chat():
            return [], ""

        clear_btn.click(clear_chat, outputs=[chatbot, current_session_id])

        # Export Chat按钮
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
                    f.write(f"# Plobi - {agent_name} Conversation Export\n")
                    f.write(f"Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

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

        # Generate Task按钮
        def generate_task(message: str, history, session_id):
            if not message.strip():
                return history, "❌ 请输入任务需求", session_id

            try:
                llm_engine = get_llm_engine()

                # Generate Task文档
                task_content = llm_engine.generate_task_document(message)

                # 在聊天历史中添加任务生成结果
                if history is None:
                    history = []

                # 添加系统消息
                history.append({"role": "assistant", "content": f"✅ 已Generate Task文档:\n\n{task_content}\n\n任务文档已保存到 `workspace/task.md`"})

                # 保存会话
                new_session_id = save_session(session_id, history)
                return history, "✅ 任务生成成功！", new_session_id
            except Exception as e:
                error_msg = f"❌ Generate Task失败: {str(e)}"
                if history is None:
                    history = []
                history.append({"role": "assistant", "content": error_msg})
                return history, error_msg, session_id

        # 添加任务状态输出文本框
        task_status = gr.Textbox(label="任务状态", visible=False)

        # 绑定任务生成事件
        task_btn.click(
            generate_task,
            inputs=[msg_input, chatbot, current_session_id],
            outputs=[chatbot, task_status, current_session_id]
        )

        # 新建聊天按钮
        new_chat_btn.click(create_new_chat, outputs=[chatbot, current_session_id])

        # 刷新侧边栏
        def refresh_sessions():
            return update_sidebar()

        refresh_btn.click(refresh_sessions, outputs=[session_list])

        # 初始化侧边栏
        session_list.children = update_sidebar()

    return panel, home_btn, chatbot, msg_input, send_btn, current_session_id


def create_glass_geek_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False, on_home_click=None) -> Tuple[gr.Column, gr.Button]:
    """创建液态玻璃风格极客面板
    Args:
        agent: Agent configuration dictionary
        models_config: Models configuration dictionary
        visible: Whether panel is visible initially
        on_home_click: Optional callback for home button click
    """
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")
    personality = agent.get("personality", "")
    system_prompt = agent.get("system_prompt", "")
    skills = agent.get("skills", [])

    with gr.Column(elem_classes="glass-agent-panel", visible=visible) as panel:
        # 面板标题
        gr.HTML(f"""
        <div class="glass-panel-header">
            <div class="agent-avatar">{DEFAULT_AVATARS.get(agent_id, "🤖")}</div>
            <div class="agent-info">
                <h3 class="agent-name">{agent_name}</h3>
                <p class="agent-role">{agent_role}</p>
            </div>
        </div>
        """)

        # Home button to return to main dashboard
        with gr.Row():
            home_btn = gr.Button("← Back to Home", variant="secondary", elem_classes="nav-btn", size="sm")
            if on_home_click:
                home_btn.click(fn=on_home_click, inputs=None, outputs=None)

        # 个性描述
        gr.Markdown(f"**Personality**: {personality}")

        # 技能栈
        if skills:
            skills_text = " | ".join(skills)
            gr.Markdown(f"**Skills**: {skills_text}")

        # 系统提示词预览
        with gr.Accordion("System Prompt", open=False):
            gr.Markdown(f"```\n{system_prompt}\n```")

        # 分隔线
        gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);'>")

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
                    return "⚠️ 未找到任务文档，请在助理面板Generate Task"

            refresh_btn = gr.Button("刷新任务文档", variant="secondary", size="sm", elem_classes="glass-btn")
            refresh_btn.click(refresh_task_document, outputs=[task_content_display])

        # 聊天区域（执行日志）
        chatbot = gr.Chatbot(
            label="",
            height=400,
            show_label=False,
            render_markdown=True,
            elem_classes="glass-chatbot"
        )

        # 输入区域
        with gr.Row():
            msg_input = gr.Textbox(
                placeholder=f"输入自定义指令或直接执行任务... (按EnterSend)",
                lines=2,
                max_lines=6,
                container=False,
                scale=9,
                elem_classes="glass-input"
            )
            send_btn = gr.Button("Send", variant="secondary", scale=1, min_width=80, elem_classes="glass-btn")

        # 功能按钮
        with gr.Row():
            clear_btn = gr.Button("清空日志", variant="secondary", elem_classes="glass-btn")
            execute_task_btn = gr.Button("🚀 执行任务", variant="primary", elem_classes="glass-btn")

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
                initial_reply = f"💻 **Geek Mode**: Analyzing your instruction..."
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
                    error_msg = "❌ 未找到任务文档，请在助理面板Generate Task"
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

                # 执行任务（简单版本，后续可改进为流式输出）
                try:
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

    return panel, home_btn


def create_glass_generic_agent_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False, on_home_click=None) -> Tuple[gr.Column, gr.Button]:
    """创建液态玻璃风格通用Agent面板
    Args:
        agent: Agent configuration dictionary
        models_config: Models configuration dictionary
        visible: Whether panel is visible initially
        on_home_click: Optional callback for home button click
    """
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")
    personality = agent.get("personality", "")
    system_prompt = agent.get("system_prompt", "")
    skills = agent.get("skills", [])

    with gr.Column(elem_classes="glass-agent-panel", visible=visible) as panel:
        # 面板标题
        gr.HTML(f"""
        <div class="glass-panel-header">
            <div class="agent-avatar">{DEFAULT_AVATARS.get(agent_id, "🤖")}</div>
            <div class="agent-info">
                <h3 class="agent-name">{agent_name}</h3>
                <p class="agent-role">{agent_role}</p>
            </div>
        </div>
        """)

        # Home button to return to main dashboard
        with gr.Row():
            home_btn = gr.Button("← Back to Home", variant="secondary", elem_classes="nav-btn", size="sm")
            if on_home_click:
                home_btn.click(fn=on_home_click, inputs=None, outputs=None)

        # 个性描述
        gr.Markdown(f"**Personality**: {personality}")

        # 技能栈
        if skills:
            skills_text = " | ".join(skills)
            gr.Markdown(f"**Skills**: {skills_text}")

        # 系统提示词预览
        with gr.Accordion("System Prompt", open=False):
            gr.Markdown(f"```\n{system_prompt}\n```")

        # 分隔线
        gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);'>")

        # 聊天区域
        chatbot = gr.Chatbot(
            label="",
            height=400,
            show_label=False,
            render_markdown=True,
            elem_classes="glass-chatbot"
        )

        # 输入区域
        with gr.Row():
            msg_input = gr.Textbox(
                placeholder=f"Chat with {agent_name}... (Press Enter to send)",
                lines=2,
                max_lines=6,
                container=False,
                scale=9,
                elem_classes="glass-input"
            )
            send_btn = gr.Button("Send", variant="secondary", scale=1, min_width=80, elem_classes="glass-btn")

        # Clear Chat按钮
        clear_btn = gr.Button("Clear Chat", variant="secondary", elem_classes="glass-btn")

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
                initial_reply = f"👋 Hello! I'm {agent_name} ({agent_role}).\n\n"
                initial_reply += f"Received your message: '{message}'\n\n"
                initial_reply += f"Based on my personality ({personality}), I'm processing your request..."

                history.append({"role": "assistant", "content": initial_reply})
                yield "", history

                # 使用LLM引擎生成流式响应
                full_response = ""
                for chunk in llm_engine.generate_stream(agent_id, message, history[:-1]):
                    full_response += chunk
                    history[-1] = {"role": "assistant", "content": initial_reply + full_response}
                    yield "", history

            except Exception as e:
                error_msg = f"❌ 处理请求失败: {str(e)}"
                if history and len(history) > 0 and history[-1].get("role") == "assistant":
                    history[-1] = {"role": "assistant", "content": error_msg}
                else:
                    history.append({"role": "assistant", "content": error_msg})
                yield "", history

        # 绑定事件
        msg_input.submit(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        send_btn.click(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        clear_btn.click(lambda: [], outputs=[chatbot])

    return panel, home_btn


def create_glass_publisher_panel(agent: Dict[str, Any], models_config: Dict[str, Any], visible: bool = False, on_home_click=None) -> Tuple[gr.Column, gr.Button]:
    """Create liquid glass Publisher agent panel with Audio Analysis Engine
    Args:
        agent: Agent configuration dictionary
        models_config: Models configuration dictionary
        visible: Whether panel is visible initially
        on_home_click: Optional callback for home button click
    Returns:
        Tuple of (panel, home_button)
    """
    agent_id = agent.get("id", "")
    agent_name = agent.get("name", "")
    agent_role = agent.get("role", "")
    personality = agent.get("personality", "")
    system_prompt = agent.get("system_prompt", "")
    skills = agent.get("skills", [])

    with gr.Column(elem_classes="glass-agent-panel", visible=visible) as panel:
        # Panel header with avatar and title
        gr.HTML(f"""
        <div class="glass-panel-header">
            <div class="agent-avatar">{DEFAULT_AVATARS.get(agent_id, "🤖")}</div>
            <div class="agent-info">
                <h3 class="agent-name">{agent_name}</h3>
                <p class="agent-role">{agent_role}</p>
            </div>
        </div>
        """)

        # Home button to return to main dashboard
        with gr.Row():
            home_btn = gr.Button("← Back to Home", variant="secondary", elem_classes="nav-btn", size="sm")
            if on_home_click:
                home_btn.click(fn=on_home_click, inputs=None, outputs=None)

        # Personality description
        gr.Markdown(f"**Personality**: {personality}")

        # Skills
        if skills:
            skills_text = " | ".join(skills)
            gr.Markdown(f"**Skills**: {skills_text}")

        # System prompt preview
        with gr.Accordion("System Prompt", open=False):
            gr.Markdown(f"```\n{system_prompt}\n```")

        # Divider
        gr.HTML("<hr style='margin: 20px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);'>")

        # ========== AUDIO ANALYSIS ENGINE SECTION ==========
        gr.Markdown("### 🎵 Audio Analysis Engine")
        gr.Markdown("Upload music tracks to extract BPM, key, and beat information.")

        # Audio upload component
        audio_input = gr.Audio(
            type="filepath",
            label="Upload Music Track",
            elem_classes=["glass-audio"]
        )

        # Analyze button
        analyze_btn = gr.Button(
            "Analyze Audio Track",
            variant="primary",
            elem_classes=["glass-btn"]
        )

        # Results display
        results_output = gr.JSON(
            label="Analysis Results"
        )

        # Divider between audio engine and chat
        gr.HTML("<hr style='margin: 30px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);'>")

        # ========== CHAT SECTION ==========
        gr.Markdown("### 💬 Content Publishing Assistant")

        # Chat area
        chatbot = gr.Chatbot(
            label="",
            height=350,
            show_label=False,
            render_markdown=True,
            elem_classes="glass-chatbot"
        )

        # Input area
        with gr.Row():
            msg_input = gr.Textbox(
                placeholder=f"Chat with {agent_name} about content publishing... (Press Enter to send)",
                lines=2,
                max_lines=6,
                container=False,
                scale=9,
                elem_classes="glass-input"
            )
            send_btn = gr.Button("Send", variant="secondary", scale=1, min_width=80, elem_classes="glass-btn")

        # Clear Chat button
        clear_btn = gr.Button("Clear Chat", variant="secondary", elem_classes="glass-btn")

        # ========== EVENT HANDLERS ==========

        # Audio analysis event handler
        def handle_audio_analysis(audio_file):
            """Handle audio file analysis"""
            if audio_file is None:
                return {"status": "error", "message": "No audio file uploaded."}

            try:
                # Call the audio analyzer tool
                result_json = analyze_audio_track(audio_file)
                result = json.loads(result_json)
                return result
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Analysis failed: {str(e)}"
                }

        # Bind analyze button to audio analysis function
        analyze_btn.click(
            fn=handle_audio_analysis,
            inputs=[audio_input],
            outputs=[results_output]
        )

        # Chat event handler (using LLM)
        def chat_handler(message: str, history):
            if not message.strip():
                return "", history

            if history is None:
                history = []

            # Gradio 6.0 format: add user message
            history.append({"role": "user", "content": message})
            yield "", history

            try:
                # Initialize LLM engine
                llm_engine = get_llm_engine()

                # Add initial reply
                initial_reply = f"👋 Hello! I'm {agent_name} ({agent_role}).\n\n"
                initial_reply += f"Received your message: '{message}'\n\n"
                initial_reply += f"Based on my personality ({personality}), I'm processing your request..."

                history.append({"role": "assistant", "content": initial_reply})
                yield "", history

                # Generate streaming response using LLM engine
                full_response = ""
                for chunk in llm_engine.generate_stream(agent_id, message, history[:-1]):
                    full_response += chunk
                    history[-1] = {"role": "assistant", "content": initial_reply + full_response}
                    yield "", history

            except Exception as e:
                error_msg = f"❌ Failed to process request: {str(e)}"
                if history and len(history) > 0 and history[-1].get("role") == "assistant":
                    history[-1] = {"role": "assistant", "content": error_msg}
                else:
                    history.append({"role": "assistant", "content": error_msg})
                yield "", history

        # Bind chat events
        msg_input.submit(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        send_btn.click(chat_handler, [msg_input, chatbot], [msg_input, chatbot])
        clear_btn.click(lambda: [], outputs=[chatbot])

    return panel, home_btn


def build_glass_ui():
    """构建液态玻璃UI"""
    # 加载配置
    agents_config = load_json_config("agents_config.json")
    models_config = load_json_config("models_config.json")

    # 获取活跃Agent
    agents = agents_config.get("agents", [])
    active_agents = [agent for agent in agents if agent.get("active", True)]

    # 液态玻璃CSS
    glass_css = """
    /* Global Reset */
    :root { --text-sm: 12px; --text-md: 14px; --text-lg: 16px; }
    .gradio-container { background: #FFFFFF !important; font-family: 'Inter', sans-serif !important; }

    /* The Glow Background */
    body::before {
        content: ''; position: fixed; top: -10%; left: -10%; width: 50%; height: 50%;
        background: radial-gradient(circle, rgba(96,177,255,0.15) 0%, rgba(255,255,255,0) 70%);
        filter: blur(100px); z-index: -1;
    }

    /* Force Remove All Gradio Default Frames */
    .gr-box, .gr-group, .gr-panel, .gradio-container .form {
        border: none !important; background: transparent !important; box-shadow: none !important;
    }

    /* Fixed Compact Navbar */
    #top-nav {
        position: fixed; top: 0; left: 0; width: 100%; height: 50px;
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 40px; background: rgba(255,255,255,0.8); backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(0,0,0,0.05); z-index: 1000;
    }

    /* Main content padding to avoid navbar overlap */
    .main-content {
        padding-top: 50px !important;
    }

    .gemini-input-wrapper {
        background: #FFFFFF !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
        border-radius: 30px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important;
        padding: 4px 16px !important;
    }

    .glass-input {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 16px !important;
        color: #000000 !important;
        padding: 0 !important;
    }
    .glass-input:focus {
        outline: none !important;
    }
    .glass-input::placeholder {
        color: rgba(0,0,0,0.4) !important;
        opacity: 0.8 !important;
    }

    .agent-card {
        background: rgba(255,255,255,0.6) !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        cursor: pointer;
    }
    .agent-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.08) !important;
    }
    """

    with gr.Blocks(
        title="Plobi - Multi-Agent System"
    ) as app:
        # Top navigation bar
        home_btn, settings_btn, models_btn, agents_btn = create_top_navbar()

        # Main content area with all panels
        with gr.Column(elem_classes="main-content"):
            # Home panel (visible by default)
            home_panel, home_input, card_buttons, agent_ids = create_home_panel(agents_config, models_config)

            # Settings panel (hidden)
            settings_panel = create_settings_panel(visible=False)

            # Models panel (hidden)
            models_panel = create_models_panel(models_config, visible=False)

            # Agent panels (hidden by default)
            agent_panels = {}
            home_buttons = {}
            # Assistant panel components for auto-routing
            assistant_chatbot = None
            assistant_msg_input = None
            assistant_send_btn = None
            assistant_session_state = None
            for agent in active_agents:
                agent_id = agent.get("id", "")
                if agent_id == "assistant":
                    # Create assistant panel with professional layout and session management
                    panel, agent_home_btn, chatbot, msg_input, send_btn, session_state = create_glass_assistant_panel(agent, models_config, visible=False)
                    assistant_chatbot = chatbot
                    assistant_msg_input = msg_input
                    assistant_send_btn = send_btn
                    assistant_session_state = session_state
                elif agent_id == "geek":
                    panel, agent_home_btn = create_glass_geek_panel(agent, models_config, visible=False)
                elif agent_id == "publisher":
                    # Create publisher panel with audio analysis engine
                    panel, agent_home_btn = create_glass_publisher_panel(agent, models_config, visible=False)
                else:
                    panel, agent_home_btn = create_glass_generic_agent_panel(agent, models_config, visible=False)
                agent_panels[agent_id] = panel
                home_buttons[agent_id] = agent_home_btn

            # Hidden component for passing home input to assistant
            home_to_assistant_msg = gr.Textbox(visible=False, interactive=False)

        # Collect all panels for routing
        all_panels = {
            "home": home_panel,
            "settings": settings_panel,
            "models": models_panel,
            **agent_panels
        }

        # Collect all outputs for routing (panels + navbar buttons)
        all_outputs = list(all_panels.values()) + [home_btn, settings_btn, models_btn]

        # Routing function: show one panel, hide others, and update active button states
        def navigate_with_active(panel_name: str):
            """Show the specified panel, hide others, and update active button states"""
            panel_updates = []
            for name, panel in all_panels.items():
                panel_updates.append(gr.update(visible=(name == panel_name)))

            # Update button variants based on active panel
            if panel_name == "home":
                home_variant = "primary"
                settings_variant = "secondary"
                models_variant = "secondary"
            elif panel_name == "settings":
                home_variant = "secondary"
                settings_variant = "primary"
                models_variant = "secondary"
            elif panel_name == "models":
                home_variant = "secondary"
                settings_variant = "secondary"
                models_variant = "primary"
            else:
                # Agent panels - no active navbar button
                home_variant = "secondary"
                settings_variant = "secondary"
                models_variant = "secondary"

            return panel_updates + [
                gr.update(variant=home_variant),
                gr.update(variant=settings_variant),
                gr.update(variant=models_variant)
            ]

        # Connect top navbar buttons
        home_btn.click(
            fn=lambda: navigate_with_active("home"),
            outputs=all_outputs
        )
        settings_btn.click(
            fn=lambda: navigate_with_active("settings"),
            outputs=all_outputs
        )
        models_btn.click(
            fn=lambda: navigate_with_active("models"),
            outputs=all_outputs
        )

        # Connect agent card clicks
        for card_btn, agent_id in zip(card_buttons, agent_ids):
            card_btn.click(
                fn=lambda agent_id=agent_id: navigate_with_active(agent_id),
                outputs=all_outputs
            )

        # Connect home buttons to return to home panel
        for home_btn in home_buttons.values():
            home_btn.click(
                fn=lambda: navigate_with_active("home"),
                outputs=all_outputs
            )

        # Auto-routing: Home input submits to Assistant panel
        if assistant_msg_input is not None:
            def handle_home_submit(message_data):
                """Route from home to assistant and prefill the input"""
                # Extract text from MultimodalTextbox tuple (text, files)
                if isinstance(message_data, tuple) and len(message_data) > 0:
                    text = message_data[0]
                else:
                    text = str(message_data) if message_data is not None else ""

                # If empty, still route but don't prefill
                if not text.strip():
                    text = ""

                # Create panel updates: hide home, show assistant
                panel_updates = []
                for name, panel in all_panels.items():
                    panel_updates.append(gr.update(visible=(name == "assistant")))

                # Navbar buttons become secondary (no active)
                button_updates = [
                    gr.update(variant="secondary"),
                    gr.update(variant="secondary"),
                    gr.update(variant="secondary")
                ]

                # Return updates: panels, buttons, prefill assistant input, set hidden message, and reset session
                return panel_updates + button_updates + [text, text, ""]

            def generate_assistant_response(text, chatbot_history, session_id):
                """Generate assistant response when home input is routed"""
                if not text.strip():
                    return chatbot_history, "", session_id  # No text, just return history and clear input

                # Add user message to history
                if chatbot_history is None:
                    chatbot_history = []
                chatbot_history.append({"role": "user", "content": text})

                # Initialize LLM engine
                from core.llm_engine import get_llm_engine
                llm_engine = get_llm_engine()

                # Generate initial placeholder
                chatbot_history.append({"role": "assistant", "content": "💭 Thinking..."})
                yield chatbot_history, "", session_id

                try:
                    # Generate stream
                    full_response = ""
                    for chunk in llm_engine.generate_stream("assistant", text, chatbot_history[:-1]):
                        full_response += chunk
                        chatbot_history[-1] = {"role": "assistant", "content": "💭 Thinking..." + full_response}
                        yield chatbot_history, "", session_id
                    
                    # Save the completed session
                    new_session_id = save_session(session_id, chatbot_history)
                    yield chatbot_history, "", new_session_id
                    
                except Exception as e:
                    chatbot_history[-1] = {"role": "assistant", "content": f"❌ Error: {str(e)}"}
                    yield chatbot_history, "", session_id

            # Home input submit triggers routing and prefills assistant input
            home_submit_outputs = all_outputs + [assistant_msg_input, home_to_assistant_msg, assistant_session_state]
            home_input.submit(
                fn=handle_home_submit,
                inputs=[home_input],
                outputs=home_submit_outputs
            )

            # When hidden message changes, trigger assistant response generation
            if assistant_chatbot is not None:
                home_to_assistant_msg.change(
                    fn=generate_assistant_response,
                    inputs=[home_to_assistant_msg, assistant_chatbot, assistant_session_state],
                    outputs=[assistant_chatbot, assistant_msg_input, assistant_session_state]
                )

    return app, glass_css


def main():
    """主函数"""
    print("=" * 60)
    print("Plobi - Liquid Glass Interface")
    print("=" * 60)
    print("服务地址: http://127.0.0.1:7860")
    print("功能特性:")
    print("  * 现代化液态玻璃设计")
    print("  * 响应式布局")
    print("  * Assistant chat interface")
    print("  * SPA routing with panel switching")
    print("  * 多Agent支持")
    print("  * 集成真实LLM引擎 (DeepSeek/Ollama/OpenAI)")
    print("  * 助理Agent任务文档生成")
    print("  * 极客Agent Open Interpreter集成")
    print("=" * 60)

    app, glass_css = build_glass_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,  # 统一使用7860端口
        share=False,
        show_error=True,
        css=glass_css,
        theme=gr.themes.Soft(),
        favicon_path=None
    )


if __name__ == "__main__":
    main()