import type { Message } from "../../store/chatStore";
import { useAgentStore } from "../../store/agentStore";
import AgentAvatar from "../agents/AgentAvatar";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const agents = useAgentStore((s) => s.agents);
  const isUser = message.role === "user";
  const agent = isUser ? undefined : agents.find((a) => a.id === message.agentId);

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <AgentAvatar agent={agent} isUser={isUser} />
      <div className={`max-w-[70%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
        {!isUser && (
          <span className="text-xs text-[var(--text-secondary)] font-medium">
            {agent?.name ?? "Agent"}
          </span>
        )}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-[var(--accent-muted)] rounded-tr-sm"
              : "bg-[var(--bg-0)] border border-[var(--border)] rounded-tl-sm"
          }`}
        >
          {message.isStreaming ? (
            <span className="streaming-cursor">{message.streamBuffer}</span>
          ) : (
            message.content
          )}
        </div>
      </div>
    </div>
  );
}
