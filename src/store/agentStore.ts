import { create } from "zustand";

export type AgentStatus = "idle" | "thinking" | "running" | "done" | "error";

export interface Agent {
  id: string;
  name: string;
  avatar: {
    type: "emoji" | "text" | "image" | "url";
    value: string;
  };
  status: AgentStatus;
  role: string;
  isCustom?: boolean;
}

interface AgentState {
  agents: Agent[];
  setAgentStatus: (id: string, status: AgentStatus) => void;
  addAgent: (agent: Agent) => void;
  removeAgent: (id: string) => void;
}

const DEFAULT_AGENTS: Agent[] = [
  { id: "master", name: "Master", avatar: { type: "emoji", value: "🧠" }, status: "idle", role: "中枢主控" },
  { id: "researcher", name: "研究员", avatar: { type: "emoji", value: "🔬" }, status: "idle", role: "信息收集" },
  { id: "engineer", name: "工程师", avatar: { type: "emoji", value: "⚙️" }, status: "idle", role: "代码执行" },
  { id: "publisher", name: "出版官", avatar: { type: "emoji", value: "📝" }, status: "idle", role: "文档生成" },
  { id: "musician", name: "音乐家", avatar: { type: "emoji", value: "🎵" }, status: "idle", role: "音频分析" },
  { id: "videographer", name: "剪辑师", avatar: { type: "emoji", value: "🎬" }, status: "idle", role: "视频剪辑" },
];

export const useAgentStore = create<AgentState>((set) => ({
  agents: DEFAULT_AGENTS,

  setAgentStatus: (id, status) =>
    set((s) => ({
      agents: s.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    })),

  addAgent: (agent) => set((s) => ({ agents: [...s.agents, agent] })),

  removeAgent: (id) => set((s) => ({ agents: s.agents.filter((a) => a.id !== id) })),
}));
