import { useState, useRef, useEffect } from "react";
import type { Session } from "../../store/chatStore";
import { useChatStore } from "../../store/chatStore";
import { useStream } from "../../hooks/useStream";
import MessageBubble from "../chat/MessageBubble";
import MessageInput from "../chat/MessageInput";

interface ChatPanelProps {
  session: Session | null;
}

export default function ChatPanel({ session }: ChatPanelProps) {
  const addMessage = useChatStore((s) => s.addMessage);
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
