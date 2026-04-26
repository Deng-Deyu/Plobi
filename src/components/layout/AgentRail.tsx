import { useAgentStore } from "../../store/agentStore";
import AgentCard from "../agents/AgentCard";

interface AgentRailProps {
  onCollapse: () => void;
}

export default function AgentRail({ onCollapse }: AgentRailProps) {
  const agents = useAgentStore((s) => s.agents);

  return (
    <div className="w-[220px] h-full flex flex-col bg-[var(--bg-1)] border-l border-[var(--border)] shrink-0">
      <div className="flex items-center justify-between px-4 h-12 border-b border-[var(--border)]">
        <span className="text-sm font-semibold">Agent 团队</span>
        <button onClick={onCollapse} className="p-1 rounded hover:bg-[var(--bg-2)]">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  );
}
