import { useState } from "react";

export default function OverlayInput() {
  const [text, setText] = useState("");

  const handleSend = async (message: string) => {
    try {
      // Emit Tauri event to main window with the message
      const { emit } = await import("@tauri-apps/api/event");
      await emit("overlay-send-message", { prompt: message });

      // Hide overlay
      const { getCurrentWebviewWindow } = await import("@tauri-apps/api/webviewWindow");
      const overlay = getCurrentWebviewWindow();
      await overlay.hide();

      // Show and focus main window
      const { WebviewWindow } = await import("@tauri-apps/api/webviewWindow");
      const mainWindow = await WebviewWindow.getByLabel("main");
      if (mainWindow) {
        await mainWindow.unminimize();
        await mainWindow.show();
        await mainWindow.setFocus();
      }
    } catch (error) {
      console.error("Overlay send error:", error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && text.trim()) {
      const message = text.trim();
      setText("");
      handleSend(message);
    }
    if (e.key === "Escape") {
      import("@tauri-apps/api/webviewWindow").then(({ getCurrentWebviewWindow }) => {
        const overlay = getCurrentWebviewWindow();
        overlay.hide();
      });
    }
  };

  return (
    <div className="glass overlay-pill flex items-center w-full h-full">
      <div className="text-xl mr-3">🧠</div>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入指令... (Enter 发送, Esc 关闭)"
        className="flex-1 bg-transparent border-none outline-none text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
        autoFocus
      />
    </div>
  );
}
