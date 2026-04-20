"""
AI OS V4.0 - 桌面悬浮总控台 (Desktop Shell)
基于 PyQt6 的沉浸式无边框窗口，支持全局热键和系统托盘
"""

import json
import logging
import os
import signal
import sys
import threading
import time
import traceback
import winreg
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from PyQt6.QtCore import (
    QPoint, QTimer, QUrl, Qt, pyqtSignal, QObject, QThread,
    QEvent
)
from PyQt6.QtGui import (
    QAction, QCloseEvent, QFocusEvent, QIcon,
    QFont, QFontDatabase
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFileDialog,
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton,
    QStyle, QSystemTrayIcon, QVBoxLayout, QWidget
)

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置路径
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
DEFAULT_SETTINGS = {
    "window": {
        "width": 1000,
        "height": 700,
        "always_on_top": True,
        "center_on_start": True,
        "auto_hide_on_focus_out": True,
        "opacity": 0.98
    },
    "hotkey": {
        "primary": "alt+/",
        "alternate": "ctrl+shift+space",
        "enabled": True,
        "release_modifier_keys": True
    },
    "system": {
        "autostart": False,
        "minimize_to_tray": True,
        "start_hidden": True,
        "check_for_updates": False
    },
    "network": {
        "server_host": "0.0.0.0",
        "server_port": 7860,
        "api_timeout": 120,
        "retry_attempts": 3
    }
}

# 开机自启注册表路径
AUTOSTART_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_REG_NAME = "AI_OS_V4_Desktop"

@dataclass
class AppSettings:
    """应用设置数据类"""
    window_width: int = 1000
    window_height: int = 700
    always_on_top: bool = True
    center_on_start: bool = True
    auto_hide_on_focus_out: bool = True
    window_opacity: float = 0.98

    hotkey_primary: str = "alt+/"
    hotkey_alternate: str = "ctrl+shift+space"
    hotkey_enabled: bool = True
    release_modifier_keys: bool = True

    autostart: bool = False
    minimize_to_tray: bool = True
    start_hidden: bool = True
    check_for_updates: bool = False

    server_host: str = "0.0.0.0"
    server_port: int = 7860
    web_url: str = "http://127.0.0.1:7860"


def load_settings() -> Tuple[AppSettings, Dict[str, Any]]:
    """
    加载并验证配置文件
    返回：(AppSettings对象, 原始配置字典)
    """
    try:
        if not SETTINGS_PATH.exists():
            logger.warning(f"配置文件不存在，创建默认配置: {SETTINGS_PATH}")
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(
                json.dumps(DEFAULT_SETTINGS, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            raw_settings = DEFAULT_SETTINGS
        else:
            content = SETTINGS_PATH.read_text(encoding="utf-8")
            raw_settings = json.loads(content)
            if not isinstance(raw_settings, dict):
                raise ValueError("配置文件必须为JSON对象")

            # 确保所有必要的键都存在
            for key, default_value in DEFAULT_SETTINGS.items():
                if key not in raw_settings:
                    raw_settings[key] = default_value
                    logger.info(f"添加缺失的配置项: {key}")

    except (json.JSONDecodeError, OSError, ValueError) as e:
        logger.error(f"配置文件加载失败，使用默认值: {e}")
        raw_settings = DEFAULT_SETTINGS
        SETTINGS_PATH.write_text(
            json.dumps(DEFAULT_SETTINGS, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # 从原始配置创建AppSettings对象
    try:
        settings = AppSettings(
            window_width=raw_settings.get("window", {}).get("width", 1000),
            window_height=raw_settings.get("window", {}).get("height", 700),
            always_on_top=raw_settings.get("window", {}).get("always_on_top", True),
            center_on_start=raw_settings.get("window", {}).get("center_on_start", True),
            auto_hide_on_focus_out=raw_settings.get("window", {}).get("auto_hide_on_focus_out", True),
            window_opacity=raw_settings.get("window", {}).get("opacity", 0.98),

            hotkey_primary=raw_settings.get("hotkey", {}).get("primary", "alt+/"),
            hotkey_alternate=raw_settings.get("hotkey", {}).get("alternate", "ctrl+shift+space"),
            hotkey_enabled=raw_settings.get("hotkey", {}).get("enabled", True),
            release_modifier_keys=raw_settings.get("hotkey", {}).get("release_modifier_keys", True),

            autostart=raw_settings.get("system", {}).get("autostart", False),
            minimize_to_tray=raw_settings.get("system", {}).get("minimize_to_tray", True),
            start_hidden=raw_settings.get("system", {}).get("start_hidden", True),
            check_for_updates=raw_settings.get("system", {}).get("check_for_updates", False),

            server_host=raw_settings.get("network", {}).get("server_host", "0.0.0.0"),
            server_port=raw_settings.get("network", {}).get("server_port", 7860),
            web_url=f"http://127.0.0.1:{raw_settings.get('network', {}).get('server_port', 7860)}"
        )
    except Exception as e:
        logger.error(f"配置解析失败，使用默认值: {e}")
        settings = AppSettings()
        raw_settings = DEFAULT_SETTINGS

    return settings, raw_settings


def save_settings(settings: AppSettings) -> None:
    """保存设置到配置文件"""
    try:
        raw_settings = {
            "window": {
                "width": settings.window_width,
                "height": settings.window_height,
                "always_on_top": settings.always_on_top,
                "center_on_start": settings.center_on_start,
                "auto_hide_on_focus_out": settings.auto_hide_on_focus_out,
                "opacity": settings.window_opacity
            },
            "hotkey": {
                "primary": settings.hotkey_primary,
                "alternate": settings.hotkey_alternate,
                "enabled": settings.hotkey_enabled,
                "release_modifier_keys": settings.release_modifier_keys
            },
            "system": {
                "autostart": settings.autostart,
                "minimize_to_tray": settings.minimize_to_tray,
                "start_hidden": settings.start_hidden,
                "check_for_updates": settings.check_for_updates
            },
            "network": {
                "server_host": settings.server_host,
                "server_port": settings.server_port,
                "api_timeout": 120,
                "retry_attempts": 3
            },
            "ui": {
                "theme": "claude",
                "font_size": 14,
                "font_family": "Inter, -apple-system, system-ui, sans-serif",
                "animation_enabled": True,
                "dark_mode": False
            }
        }

        SETTINGS_PATH.write_text(
            json.dumps(raw_settings, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        logger.info("设置已保存")
    except Exception as e:
        logger.error(f"保存设置失败: {e}")
        raise


def convert_hotkey_to_pynput(hotkey: str) -> str:
    """
    将用户友好的热键格式转换为pynput格式
    示例:
    "alt+/" -> "<alt>+/"
    "ctrl+shift+space" -> "<ctrl>+<shift>+space"
    """
    if not hotkey:
        return hotkey

    # 定义修饰键映射
    modifiers = {
        'ctrl': '<ctrl>',
        'control': '<ctrl>',
        'alt': '<alt>',
        'shift': '<shift>',
        'win': '<cmd>',  # Windows键
        'cmd': '<cmd>',
        'command': '<cmd>'
    }

    # 分割热键
    parts = hotkey.lower().split('+')
    converted_parts = []

    for part in parts:
        part_stripped = part.strip()
        # 检查是否是修饰键
        if part_stripped in modifiers:
            converted_parts.append(modifiers[part_stripped])
        else:
            # 非修饰键，保持原样（pynput支持普通键名）
            converted_parts.append(part_stripped)

    return '+'.join(converted_parts)


class HotkeyManager(QObject):
    """全局热键管理器"""

    hotkey_triggered = pyqtSignal()

    def __init__(self, hotkey: str = "alt+/"):
        super().__init__()
        self.original_hotkey = hotkey
        self.pynput_hotkey = convert_hotkey_to_pynput(hotkey)
        self._listener = None
        self._running = False
        self._thread = None

    def start(self) -> bool:
        """启动热键监听"""
        if self._running:
            logger.warning("热键监听器已在运行")
            return True

        try:
            # 尝试导入pynput
            from pynput import keyboard as pynput_keyboard

            def hotkey_listener():
                """热键监听线程函数"""
                try:
                    with pynput_keyboard.GlobalHotKeys({
                        self.pynput_hotkey: self._on_hotkey_pressed
                    }) as listener:
                        self._listener = listener
                        listener.join()
                except Exception as e:
                    logger.error(f"热键监听线程异常: {type(e).__name__}: {e}")
                    import traceback
                    logger.error(f"异常详情: {traceback.format_exc()}")

            self._thread = threading.Thread(target=hotkey_listener, daemon=True)
            self._thread.start()
            self._running = True
            logger.info(f"全局热键已启用: {self.original_hotkey} (pynput格式: {self.pynput_hotkey})")
            return True

        except ImportError as e:
            logger.error(f"pynput库未安装，无法启用全局热键: {e}")
            logger.info("请运行: pip install pynput")
            return False
        except Exception as e:
            logger.error(f"热键启动失败: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"异常详情: {traceback.format_exc()}")
            return False

    def stop(self) -> None:
        """停止热键监听"""
        self._running = False
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception as e:
                logger.error(f"停止热键监听器失败: {e}")
        self._listener = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        logger.info("热键监听器已停止")

    def _on_hotkey_pressed(self) -> None:
        """热键被按下时的回调"""
        logger.debug(f"热键触发: {self.original_hotkey}")
        self.hotkey_triggered.emit()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class TitleBar(QWidget):
    """自定义标题栏，支持拖拽窗口"""

    def __init__(self, parent_window: QMainWindow):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self._drag_start_pos: Optional[QPoint] = None
        self._window_start_pos: Optional[QPoint] = None

        self.setFixedHeight(30)
        self.setObjectName("titleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # 标题
        self.title_label = QLabel("AI OS V4.0 - 总控台")
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        # 最小化按钮
        self.min_button = QPushButton("−")
        self.min_button.setObjectName("titleBarButton")
        self.min_button.setFixedSize(24, 24)
        self.min_button.clicked.connect(self.parent_window.hide)

        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("titleBarButton")
        self.close_button.setFixedSize(24, 24)
        self.close_button.clicked.connect(self.parent_window.close)

        layout.addWidget(self.min_button)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint()
            self._window_start_pos = self.parent_window.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽窗口"""
        if (self._drag_start_pos is not None and
            self._window_start_pos is not None and
            event.buttons() & Qt.MouseButton.LeftButton):

            delta = event.globalPosition().toPoint() - self._drag_start_pos
            new_pos = self._window_start_pos + delta
            self.parent_window.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖拽"""
        self._drag_start_pos = None
        self._window_start_pos = None
        super().mouseReleaseEvent(event)


class DesktopOS(QMainWindow):
    """AI OS V4.0 桌面悬浮总控台"""

    def __init__(self):
        super().__init__()
        self.app_name = "AI OS V4.0"

        # 加载配置
        self.settings, self.raw_settings = load_settings()
        logger.info(f"配置加载完成: {self.settings}")

        # 状态变量
        self._quitting = False
        self._hotkey_manager: Optional[HotkeyManager] = None

        # 初始化UI
        self._init_ui()
        self._init_tray()
        self._init_hotkey()

        # 初始状态
        if self.settings.start_hidden:
            self.hide()
        else:
            self.show()
        self._sync_tray_labels()

        logger.info("AI OS V4.0 桌面悬浮总控台初始化完成")

    def _init_ui(self) -> None:
        """初始化用户界面"""
        self.setWindowTitle(self.app_name)
        self.setFixedSize(self.settings.window_width, self.settings.window_height)

        # 窗口标志
        window_flags = Qt.WindowType.FramelessWindowHint
        if self.settings.always_on_top:
            window_flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(window_flags)

        # 设置透明度
        self.setWindowOpacity(self.settings.window_opacity)

        # 创建主窗口
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加标题栏
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # 创建主内容区域
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 添加Web视图
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(self.settings.web_url))
        content_layout.addWidget(self.web_view)

        main_layout.addWidget(content_frame)

        # 应用样式
        self._apply_styles()

        # 居中显示
        if self.settings.center_on_start:
            self._center_window()

    def _apply_styles(self) -> None:
        """应用CSS样式"""
        style_sheet = """
        QWidget#centralWidget {
            background-color: #ffffff;
        }

        QFrame#contentFrame {
            border: none;
            background-color: #ffffff;
        }

        QWidget#titleBar {
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
        }

        QLabel#titleLabel {
            color: #334155;
            font-size: 13px;
            font-weight: 600;
            font-family: 'Inter', -apple-system, system-ui, sans-serif;
        }

        QPushButton#titleBarButton {
            background-color: transparent;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            color: #64748b;
            font-size: 12px;
            font-weight: 600;
        }

        QPushButton#titleBarButton:hover {
            background-color: #f1f5f9;
            border-color: #cbd5e1;
        }

        QPushButton#titleBarButton:pressed {
            background-color: #e2e8f0;
        }
        """
        self.setStyleSheet(style_sheet)

    def _center_window(self) -> None:
        """将窗口居中显示"""
        screen = QApplication.primaryScreen()
        if not screen:
            return

        screen_geo = screen.availableGeometry()
        x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
        y = screen_geo.y() + (screen_geo.height() - self.height()) // 2
        self.move(x, y)

    def _init_tray(self) -> None:
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)

        # 设置托盘图标
        app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip(self.app_name)

        # 创建托盘菜单
        tray_menu = QMenu()

        # 显示/隐藏
        self.toggle_action = QAction("显示工作台", self)
        self.toggle_action.triggered.connect(self.toggle_window)
        tray_menu.addAction(self.toggle_action)

        # 开机自启
        self.autostart_action = QAction("开机自启", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self._is_autostart_enabled())
        self.autostart_action.triggered.connect(self._on_autostart_toggled)
        tray_menu.addAction(self.autostart_action)

        tray_menu.addSeparator()

        # 退出
        quit_action = QAction("退出系统", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

        logger.info("系统托盘已初始化")

    def _init_hotkey(self) -> None:
        """初始化全局热键"""
        if not self.settings.hotkey_enabled:
            logger.info("全局热键已禁用")
            return

        self._hotkey_manager = HotkeyManager(self.settings.hotkey_primary)
        self._hotkey_manager.hotkey_triggered.connect(self._on_hotkey_triggered)

        if not self._hotkey_manager.start():
            logger.warning("全局热键启动失败")
            self._hotkey_manager = None

    def _on_hotkey_triggered(self) -> None:
        """热键触发事件处理"""
        logger.debug("热键触发，切换窗口显示状态")

        # 防卡死处理：释放修饰键
        if self.settings.release_modifier_keys:
            self._release_modifier_keys()

        # 切换窗口显示状态
        self.toggle_window()

        # 如果窗口显示，激活并聚焦
        if self.isVisible():
            self.activateWindow()
            self.raise_()
            self.web_view.setFocus()

    def _release_modifier_keys(self) -> None:
        """释放修饰键（Alt, Ctrl, Shift等）"""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            KEYEVENTF_KEYUP = 0x0002

            # 释放Alt键
            user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)
            # 释放Ctrl键
            user32.keybd_event(0x11, 0, KEYEVENTF_KEYUP, 0)
            # 释放Shift键
            user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, 0)

            logger.debug("修饰键已释放")
        except Exception as e:
            logger.warning(f"释放修饰键失败: {e}")

    def _sync_tray_labels(self) -> None:
        """同步托盘菜单标签"""
        if self.isVisible():
            self.toggle_action.setText("隐藏工作台")
        else:
            self.toggle_action.setText("显示工作台")

        # 更新开机自启状态
        self.autostart_action.blockSignals(True)
        self.autostart_action.setChecked(self._is_autostart_enabled())
        self.autostart_action.blockSignals(False)

    def toggle_window(self) -> None:
        """切换窗口显示/隐藏状态"""
        if self.isVisible():
            self.hide()
            logger.debug("窗口已隐藏")
        else:
            self._center_window()
            self.show()
            self.activateWindow()
            self.raise_()
            self.web_view.setFocus()
            logger.debug("窗口已显示")

        self._sync_tray_labels()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """失去焦点事件 - 自动隐藏窗口"""
        super().focusOutEvent(event)

        if (not self._quitting and
            self.isVisible() and
            self.settings.auto_hide_on_focus_out):

            # 检查焦点是否移到了窗口外的其他位置
            focus_widget = QApplication.focusWidget()
            if focus_widget and not self.isAncestorOf(focus_widget):
                self.hide()
                self._sync_tray_labels()
                logger.debug("失去焦点，窗口已隐藏")

    def showEvent(self, event) -> None:
        """显示事件"""
        super().showEvent(event)
        self._sync_tray_labels()

    def closeEvent(self, event: QCloseEvent) -> None:
        """关闭事件 - 隐藏而非关闭"""
        if self._quitting:
            event.accept()
            return

        if self.settings.minimize_to_tray:
            self.hide()
            self._sync_tray_labels()
            event.ignore()
        else:
            self.quit_application()
            event.accept()

    def _on_tray_activated(self, reason):
        """托盘图标激活事件"""
        # PyQt6中reason是ActivationReason枚举
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.toggle_window()

    def _autostart_command(self) -> str:
        """获取开机自启命令"""
        python_exe = os.path.abspath(sys.executable)
        script_path = os.path.abspath(Path(__file__))
        return f'"{python_exe}" "{script_path}"'

    def _is_autostart_enabled(self) -> bool:
        """检查是否启用了开机自启"""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                AUTOSTART_REG_PATH,
                0,
                winreg.KEY_READ
            ) as key:
                value, _ = winreg.QueryValueEx(key, AUTOSTART_REG_NAME)
                return value == self._autostart_command()
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"读取开机自启状态失败: {e}")
            return False

    def _set_autostart_enabled(self, enabled: bool) -> None:
        """设置开机自启状态"""
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_PATH) as key:
                if enabled:
                    winreg.SetValueEx(
                        key, AUTOSTART_REG_NAME, 0,
                        winreg.REG_SZ, self._autostart_command()
                    )
                    logger.info("开机自启已启用")
                else:
                    try:
                        winreg.DeleteValue(key, AUTOSTART_REG_NAME)
                        logger.info("开机自启已禁用")
                    except FileNotFoundError:
                        pass
        except Exception as e:
            logger.error(f"设置开机自启失败: {e}")
            raise

    def _on_autostart_toggled(self, checked: bool) -> None:
        """开机自启切换事件"""
        try:
            self._set_autostart_enabled(checked)
        except Exception as e:
            QMessageBox.warning(self, "操作失败", f"设置开机自启失败:\n{e}")
            # 恢复复选框状态
            self.autostart_action.blockSignals(True)
            self.autostart_action.setChecked(not checked)
            self.autostart_action.blockSignals(False)

    def quit_application(self) -> None:
        """安全退出应用"""
        if self._quitting:
            return

        logger.info("正在安全退出应用...")
        self._quitting = True

        # 停止热键监听
        if self._hotkey_manager is not None:
            self._hotkey_manager.stop()
            self._hotkey_manager = None

        # 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()

        # 退出应用
        QApplication.quit()

        logger.info("应用已退出")


def main() -> None:
    """应用主入口"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("AI OS V4.0")
    app.setApplicationDisplayName("Plobi")

    # 设置信号处理器，支持Ctrl+C
    def signal_handler(signum, frame):
        logger.info("\n收到中断信号，准备退出...")
        QTimer.singleShot(0, lambda: desktop.quit_application() if 'desktop' in locals() else app.quit())

    signal.signal(signal.SIGINT, signal_handler)

    # 创建定时器，允许Python处理信号
    signal_timer = QTimer()
    signal_timer.setInterval(200)
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start()

    # 创建主窗口
    desktop = DesktopOS()

    # 应用退出时的清理
    def on_about_to_quit():
        logger.info("应用正在退出，执行清理...")
        desktop.quit_application()

    app.aboutToQuit.connect(on_about_to_quit)

    # 启动信息
    print("=" * 60)
    print("AI OS V4.0 - 桌面悬浮总控台")
    print("=" * 60)
    print(f"工作台地址: {desktop.settings.web_url}")
    print(f"全局热键: {desktop.settings.hotkey_primary} (已启用)" if desktop.settings.hotkey_enabled else "全局热键: 已禁用")
    print(f"窗口尺寸: {desktop.settings.window_width}×{desktop.settings.window_height}")
    print(f"开机自启: {'已启用' if desktop._is_autostart_enabled() else '已禁用'}")
    print("=" * 60)
    print("应用已启动，请检查系统托盘图标")
    print("使用 Ctrl+C 或托盘菜单退出应用")
    print("=" * 60)

    try:
        exit_code = app.exec()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"应用主循环异常: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()