import type { Agent } from "../../store/agentStore";
import AgentStatusBadge from "./AgentStatusBadge";

interface AgentCardProps {
  agent: Agent;
}

export default function AgentCard({ agent }: AgentCardProps) {
  const mcpServers = agent.mcpServers ?? [];

  return (
    <div className="p-3 rounded-xl border border-[var(--border)] bg-[var(--bg-0)] hover:border-[var(--accent)]/30 transition-colors cursor-pointer">
      <div className="flex items-center gap-3">
        <div className="text-2xl">{agent.avatar.type === "emoji" ? agent.avatar.value : "🤖"}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">{agent.name}</span>
            <AgentStatusBadge status={agent.status} />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-[var(--text-muted)]">{agent.role}</span>
            {mcpServers.length > 0 && (
              <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-[var(--accent)]/10 text-[var(--accent)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
                {mcpServers.length} MCP
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
