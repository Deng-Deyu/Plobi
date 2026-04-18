# 文件位置：/AI_Auto_System/core/theme.py
import gradio as gr

def get_custom_theme():
    """
    基于默认 Soft 主题重写，注入 Notion/Claude 的极简风格
    使用系统无衬线字体序列保证跨平台的一致且现代的排版
    """
    return gr.themes.Soft(
        primary_hue="slate",
        secondary_hue="zinc",
        neutral_hue="gray",
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
    ).set(
        body_background_fill="#fefefe",         # 纯净白底
        body_background_fill_dark="#121212",    # 暗黑模式适配
        block_background_fill="transparent",    # 去除 block 默认底色
        block_border_width="0px",               # 无边框设计
        block_label_background_fill="transparent",
        button_primary_background_fill="#2563eb",
        button_primary_text_color="white",
        shadow_drop="none",                     # 默认去阴影，CSS 中自定义柔和阴影
    )

# 自定义 CSS 注入
CUSTOM_CSS = """
/* 彻底隐藏底部 Powered by Gradio */
footer { display: none !important; }

/* 聊天区域整体留白与软阴影优化 */
.gradio-container {
    max-width: 1200px !important; 
    margin: 0 auto !important;
}

/* 输入框 Group 软阴影 (Notion 风格) */
#input-group {
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05) !important;
    border: 1px solid #f1f1f1 !important;
    border-radius: 12px !important;
    background: white;
    padding: 8px !important;
}

/* 优化 Claude 风格聊天气泡 */
.message.bot {
    background-color: transparent !important;
    border: none !important;
    padding-left: 0 !important;
}
.message.user {
    background-color: #f4f4f5 !important; /* 浅灰底色 */
    border: 1px solid #e4e4e7 !important;
    border-radius: 12px !important;
}

/* 移动端自适应: 紧凑的内边距 */
@media (max-width: 768px) {
    .gradio-container { padding: 10px !important; }
    #input-group { padding: 4px !important; }
    .message { font-size: 14px !important; }
}
"""