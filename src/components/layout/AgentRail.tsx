import { useEffect } from "react";
import { useAgentConfigStore } from "../../store/agentConfigStore";
import { useSettingsStore } from "../../store/settingsStore";
import AgentCard from "../agents/AgentCard";
import type { Agent } from "../../store/agentStore";

interface AgentRailProps {
  onCollapse: () => void;
  onOpenConfig: () => void;
  onOpenPlugins: () => void;
  onOpenSandbox: () => void;
}

// Convert AgentConfig to Agent format for AgentCard
function convertToAgent(config: ReturnType<typeof useAgentConfigStore.getState>["agents"][number]): Agent {
  return {
    id: config.id,
    name: config.name,
    avatar: {
      type: config.avatar.type as "emoji" | "text" | "image" | "url",
      value: config.avatar.value,
    },
    status: config.is_active ? "idle" : "done",
    role: config.persona.description.slice(0, 12) || "Agent",
    mcpServers: config.mcp_servers,
    isCustom: config.created_at !== 0,
  };
}

export default function AgentRail({ onCollapse, onOpenConfig, onOpenPlugins, onOpenSandbox }: AgentRailProps) {
  const backendPort = useSettingsStore((s) => s.backendPort);
  const agents = useAgentConfigStore((s) => s.agents);
  const fetchAgents = useAgentConfigStore((s) => s.fetchAgents);

  // Fetch agents on mount
  useEffect(() => {
    fetchAgents(backendPort);
  }, [backendPort, fetchAgents]);

  return (
    <div className="w-[220px] h-full flex flex-col bg-[var(--bg-1)] border-l border-[var(--border)] shrink-0">
      <div className="flex items-center justify-between px-4 h-12 border-b border-[var(--border)]">
        <span className="text-sm font-semibold">Agent 团队</span>
        <div className="flex items-center gap-1">
          <button onClick={onOpenConfig} className="p-1 rounded hover:bg-[var(--bg-2)]" title="Agent 配置">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
          <button onClick={onOpenSandbox} className="p-1 rounded hover:bg-[var(--bg-2)]" title="代码执行">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
            </svg>
          </button>
          <button onClick={onOpenPlugins} className="p-1 rounded hover:bg-[var(--bg-2)]" title="插件管理">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2l2 7h7l-5.5 4 2 7L12 16l-5.5 4 2-7L3 9h7z" />
            </svg>
          </button>
          <button onClick={onCollapse} className="p-1 rounded hover:bg-[var(--bg-2)]">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {agents.map((agentConfig) => (
          <AgentCard key={agentConfig.id} agent={convertToAgent(agentConfig)} />
        ))}
      </div>
    </div>
  );
}
