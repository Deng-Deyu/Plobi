"""
CLI 工具自动检测脚本
Phase 3: CLI 工具封装

运行此脚本自动检测本机已安装的工具并更新 cli_whitelist.json
"""

import sys
import json
import platform
import shutil
import subprocess
from pathlib import Path


def check_command_exists(command: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(command) is not None


def check_npx_exists() -> bool:
    """检查 npx 是否存在"""
    return check_command_exists("npx")


def check_marp_available() -> bool:
    """检查 Marp CLI 是否可用（通过 npx）"""
    if not check_npx_exists():
        return False
    try:
        result = subprocess.run(
            ["npx", "-y", "@marp-team/marp-cli", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_tools() -> dict:
    """检测所有工具的安装状态"""
    platform_name = platform.system().lower()

    results = {
        "python": {
            "installed": True,
            "paths": {
                "windows": sys.executable,
                "darwin": sys.executable,
                "linux": sys.executable
            }
        },
        "npx": {
            "installed": check_npx_exists(),
            "paths": {
                "windows": "npx",
                "darwin": "npx",
                "linux": "npx"
            }
        },
        "marp": {
            "installed": check_marp_available(),
            "paths": {
                "windows": "npx",
                "darwin": "npx",
                "linux": "npx"
            }
        },
        "ffmpeg": {
            "installed": check_command_exists("ffmpeg"),
            "paths": {
                "windows": "ffmpeg",
                "darwin": "/usr/local/bin/ffmpeg",
                "linux": "/usr/bin/ffmpeg"
            }
        },
        "pandoc": {
            "installed": check_command_exists("pandoc"),
            "paths": {
                "windows": "pandoc",
                "darwin": "/usr/local/bin/pandoc",
                "linux": "/usr/bin/pandoc"
            }
        }
    }

    return results


def update_whitelist(whitelist_path: Path) -> None:
    """更新白名单配置文件"""
    if not whitelist_path.exists():
        print(f"错误: 白名单文件不存在: {whitelist_path}")
        return

    with open(whitelist_path, "r", encoding="utf-8") as f:
        whitelist = json.load(f)

    detection_results = detect_tools()
    tools = whitelist.get("tools", {})

    updated_count = 0
    for tool_name, tool_config in tools.items():
        if tool_name in detection_results:
            result = detection_results[tool_name]
            old_installed = tool_config.get("installed", False)
            new_installed = result["installed"]

            # 更新安装状态
            tool_config["installed"] = new_installed

            # 更新路径（如果检测到）
            if new_installed and "paths" in result:
                tool_config["paths"] = result["paths"]

            if old_installed != new_installed:
                status = "已安装" if new_installed else "未安装"
                print(f"  [{tool_name}] {status}")
                updated_count += 1

    # 保存更新后的配置
    with open(whitelist_path, "w", encoding="utf-8") as f:
        json.dump(whitelist, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 检测完成，更新了 {updated_count} 个工具的状态")
    print(f"✓ 配置文件已更新: {whitelist_path}")


def main():
    """主函数"""
    script_dir = Path(__file__).resolve().parent
    whitelist_path = script_dir.parent / "config" / "cli_whitelist.json"

    print("=" * 50)
    print("CLI 工具自动检测")
    print("=" * 50)
    print(f"平台: {platform.system()} {platform.release()}")
    print(f"Python: {sys.executable}")
    print(f"配置文件: {whitelist_path}")
    print("-" * 50)

    update_whitelist(whitelist_path)


if __name__ == "__main__":
    main()
