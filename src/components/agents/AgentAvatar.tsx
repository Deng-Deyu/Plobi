import type { Agent } from "../../store/agentStore";

interface AgentAvatarProps {
  agent?: Agent;
  isUser: boolean;
}

export default function AgentAvatar({ agent, isUser }: AgentAvatarProps) {
  if (isUser) {
    return (
      <div className="w-8 h-8 rounded-full bg-[var(--accent)] flex items-center justify-center text-white text-xs font-bold shrink-0">
        你
      </div>
    );
  }

  const emoji = agent?.avatar.type === "emoji" ? agent.avatar.value : "🤖";

  return (
    <div className="w-8 h-8 rounded-full bg-[var(--bg-2)] flex items-center justify-center text-lg shrink-0">
      {emoji}
    </div>
  );
}
