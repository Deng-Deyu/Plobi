import { useState } from "react";

export default function OverlayInput() {
  const [text, setText] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && text.trim()) {
      // TODO: Send to Master Agent via Tauri event, then show main window
      setText("");
      // Hide overlay after sending
      import("@tauri-apps/api/window").then(({ getCurrent }) => {
        getCurrent().hide();
      });
    }
    if (e.key === "Escape") {
      import("@tauri-apps/api/window").then(({ getCurrent }) => {
        getCurrent().hide();
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
