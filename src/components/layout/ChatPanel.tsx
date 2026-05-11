import { useRef, useEffect } from "react";
import type { Session } from "../../store/chatStore";
import { useChatStore } from "../../store/chatStore";
import { useSettingsStore } from "../../store/settingsStore";
import { useStream } from "../../hooks/useStream";
import MessageBubble from "../chat/MessageBubble";
import MessageInput from "../chat/MessageInput";

interface ChatPanelProps {
  session: Session | null;
}

export default function ChatPanel({ session }: ChatPanelProps) {
  const addMessage = useChatStore((s) => s.addMessage);
  const updateSessionTitle = useChatStore((s) => s.updateSessionTitle);
  const backendPort = useSettingsStore((s) => s.backendPort);
  const { startStream } = useStream();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages.length]);

  const handleSend = async (text: string) => {
    if (!session) return;

    // Add user message
    addMessage(session.id, {
      id: crypto.randomUUID(),
      sessionId: session.id,
      agentId: "user",
      role: "user",
      content: text,
      streamBuffer: "",
      isStreaming: false,
      attachments: [],
      timestamp: Date.now(),
    });

    // Auto-update title if this is the first message
    if (session.messages.length === 0) {
      const title = text.length > 20 ? text.slice(0, 20) + "..." : text;
      updateSessionTitle(session.id, title);
      // Also update on backend
      fetch(`http://127.0.0.1:${backendPort}/sessions/${session.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      }).catch(() => {});
    }

    // Immediately scroll to bottom
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);

    // Start streaming from Master Agent
    await startStream({
      sessionId: session.id,
      agentId: "master",
      prompt: text,
    });
  };

  if (!session) {
    return (
      <div className="flex-1 flex items-center justify-center text-[var(--text-muted)]">
        <div className="text-center">
          <div className="text-4xl mb-4">🧠</div>
          <p className="text-lg font-medium">Plobi Agent</p>
          <p className="text-sm mt-2">点击「新建对话」开始</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {session.messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <MessageInput onSend={handleSend} />
    </div>
  );
}
