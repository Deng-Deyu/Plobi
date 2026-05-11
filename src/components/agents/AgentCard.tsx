import type { Agent } from "../../store/agentStore";
import AgentStatusBadge from "./AgentStatusBadge";
import AgentAvatar from "./AgentAvatar";
import { ChevronRight } from "lucide-react";
import { getSkillColor } from "../../lib/skills";

interface AgentCardProps {
  agent: Agent;
  onClick?: () => void;
}

export default function AgentCard({ agent, onClick }: AgentCardProps) {
  const mcpServers = agent.mcpServers ?? [];

  return (
    <div
      onClick={onClick}
      className="p-3 rounded-xl border border-[var(--border)] bg-[var(--bg-0)] hover:border-[var(--accent)]/30 hover:shadow-sm transition-all cursor-pointer group"
    >
      <div className="flex items-center gap-3">
        <AgentAvatar
          name={agent.name}
          avatarType={agent.avatar.type === "image" || agent.avatar.type === "url" ? "image" : "initials"}
          avatarValue={agent.avatar.type === "image" || agent.avatar.type === "url" ? agent.avatar.value : undefined}
          size="md"
        />
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
          {agent.skills && agent.skills.length > 0 && (
            <div className="flex items-center gap-1 mt-1">
              {agent.skills.slice(0, 2).map((skill) => (
                <span
                  key={skill}
                  className="px-1.5 py-0.5 rounded text-[10px] font-medium text-white"
                  style={{ backgroundColor: getSkillColor(skill) }}
                >
                  {skill}
                </span>
              ))}
              {agent.skills.length > 2 && (
                <span className="text-[10px] text-[var(--text-muted)]">+{agent.skills.length - 2}</span>
              )}
            </div>
          )}
        </div>
        {/* Chevron hint on hover */}
        <ChevronRight
          size={14}
          className="text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
        />
      </div>
    </div>
  );
}
