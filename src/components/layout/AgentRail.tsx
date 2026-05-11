import { useEffect, useState } from "react";
import { useAgentConfigStore } from "../../store/agentConfigStore";
import { useSettingsStore } from "../../store/settingsStore";
import AgentCard from "../agents/AgentCard";
import AgentDrawer from "../agents/AgentDrawer";
import type { Agent } from "../../store/agentStore";
import { Settings, Code2, Puzzle, ChevronRight } from "lucide-react";

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
    skills: config.skills,
    mcpServers: config.mcp_servers,
    isCustom: config.created_at !== 0,
  };
}

export default function AgentRail({ onCollapse, onOpenConfig, onOpenPlugins, onOpenSandbox }: AgentRailProps) {
  const backendPort = useSettingsStore((s) => s.backendPort);
  const agents = useAgentConfigStore((s) => s.agents);
  const fetchAgents = useAgentConfigStore((s) => s.fetchAgents);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  // Fetch agents on mount
  useEffect(() => {
    fetchAgents(backendPort);
  }, [backendPort, fetchAgents]);

  return (
    <>
      <div className="w-[220px] h-full flex flex-col bg-[var(--bg-1)] border-l border-[var(--border)] shrink-0">
        <div className="flex items-center justify-between px-4 h-12 border-b border-[var(--border)]">
          <span className="text-sm font-semibold">Agent 团队</span>
          <div className="flex items-center gap-1">
            <button onClick={onOpenConfig} className="p-1 rounded hover:bg-[var(--bg-2)]" title="Agent 配置">
              <Settings size={14} />
            </button>
            <button onClick={onOpenSandbox} className="p-1 rounded hover:bg-[var(--bg-2)]" title="代码执行">
              <Code2 size={14} />
            </button>
            <button onClick={onOpenPlugins} className="p-1 rounded hover:bg-[var(--bg-2)]" title="插件管理">
              <Puzzle size={14} />
            </button>
            <button onClick={onCollapse} className="p-1 rounded hover:bg-[var(--bg-2)]">
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {agents.map((agentConfig) => {
            const agent = convertToAgent(agentConfig);
            return (
              <AgentCard
                key={agentConfig.id}
                agent={agent}
                onClick={() => setSelectedAgent(agent)}
              />
            );
          })}
        </div>
      </div>

      {/* Agent Drawer */}
      {selectedAgent && (
        <AgentDrawer
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          onOpenConfig={onOpenConfig}
        />
      )}
    </>
  );
}
