import { create } from "zustand";

// ─── Types ────────────────────────────────────────────────

export interface AvatarConfig {
  type: "initials" | "image" | "url" | "emoji"; // image preferred; emoji/url are legacy
  value: string;
}

export interface PersonaConfig {
  description: string;
  tone: string;
  greeting: string;
}

export interface ModelConfig {
  provider: string;
  model_id: string;
  temperature: number;
  max_tokens: number;
}

export interface AgentConfig {
  id: string;
  name: string;
  avatar: AvatarConfig;
  persona: PersonaConfig;
  model: ModelConfig;
  skills: string[];
  mcp_servers: string[];
  is_active: boolean;
  created_at: number;
}

export interface AgentMemory {
  key: string;
  agent_id: string;
  memory_key: string;
  value: string;
  category: string;
  created_at: number;
}

// ─── Store ────────────────────────────────────────────────

interface AgentConfigState {
  agents: AgentConfig[];
  selectedAgentId: string | null;
  memories: AgentMemory[];
  isLoading: boolean;

  // Actions
  fetchAgents: (port: number) => Promise<void>;
  selectAgent: (id: string) => void;
  updateAgent: (port: number, id: string, data: Partial<AgentConfig>) => Promise<void>;
  fetchMemories: (port: number, agentId: string) => Promise<void>;
  addMemory: (port: number, agentId: string, memoryKey: string, value: string, category: string) => Promise<void>;
  deleteMemory: (port: number, agentId: string, memoryKey: string) => Promise<void>;
}

export const useAgentConfigStore = create<AgentConfigState>((set, get) => ({
  agents: [],
  selectedAgentId: null,
  memories: [],
  isLoading: false,

  fetchAgents: async (port: number) => {
    set({ isLoading: true });
    try {
      const res = await fetch(`http://127.0.0.1:${port}/agents`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const agents: AgentConfig[] = await res.json();
      set({ agents, isLoading: false });
    } catch (err) {
      console.error("[AgentConfigStore] Failed to fetch agents from backend:", err);
      // Fallback: if agents list is empty, use hardcoded defaults so the UI isn't blank
      if (get().agents.length === 0) {
        const fallbackAgents: AgentConfig[] = [
          { id: "master", name: "Master", avatar: { type: "emoji", value: "🧠" }, persona: { description: "中枢主控", tone: "专业", greeting: "" }, model: { provider: "deepseek", model_id: "deepseek-chat", temperature: 0.7, max_tokens: 4096 }, skills: [], mcp_servers: [], is_active: true, created_at: 0 },
          { id: "researcher", name: "研究员", avatar: { type: "emoji", value: "🔬" }, persona: { description: "信息收集", tone: "严谨", greeting: "" }, model: { provider: "deepseek", model_id: "deepseek-chat", temperature: 0.5, max_tokens: 4096 }, skills: [], mcp_servers: [], is_active: true, created_at: 0 },
          { id: "engineer", name: "工程师", avatar: { type: "emoji", value: "⚙️" }, persona: { description: "代码执行", tone: "技术", greeting: "" }, model: { provider: "deepseek", model_id: "deepseek-coder", temperature: 0.3, max_tokens: 8192 }, skills: [], mcp_servers: [], is_active: true, created_at: 0 },
          { id: "publisher", name: "出版官", avatar: { type: "emoji", value: "📝" }, persona: { description: "文档生成", tone: "专业", greeting: "" }, model: { provider: "anthropic", model_id: "claude-opus-4-5", temperature: 0.8, max_tokens: 4096 }, skills: [], mcp_servers: [], is_active: true, created_at: 0 },
          { id: "musician", name: "音乐家", avatar: { type: "emoji", value: "🎵" }, persona: { description: "音频分析", tone: "热情", greeting: "" }, model: { provider: "anthropic", model_id: "claude-opus-4-5", temperature: 0.8, max_tokens: 4096 }, skills: [], mcp_servers: [], is_active: true, created_at: 0 },
          { id: "videographer", name: "剪辑师", avatar: { type: "emoji", value: "🎬" }, persona: { description: "视频剪辑", tone: "创意", greeting: "" }, model: { provider: "deepseek", model_id: "deepseek-chat", temperature: 0.7, max_tokens: 4096 }, skills: [], mcp_servers: [], is_active: true, created_at: 0 },
        ];
        set({ agents: fallbackAgents, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    }
  },

  selectAgent: (id: string) => {
    set({ selectedAgentId: id });
  },

  updateAgent: async (port: number, id: string, data: Partial<AgentConfig>) => {
    try {
      await fetch(`http://127.0.0.1:${port}/agents/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      // Refresh agents list
      await get().fetchAgents(port);
    } catch (error) {
      console.error("Failed to update agent:", error);
    }
  },

  fetchMemories: async (port: number, agentId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/agents/${agentId}/memories`);
      const memories: AgentMemory[] = await res.json();
      set({ memories });
    } catch {
      set({ memories: [] });
    }
  },

  addMemory: async (port: number, agentId: string, memoryKey: string, value: string, category: string) => {
    try {
      await fetch(`http://127.0.0.1:${port}/agents/${agentId}/memories`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ memory_key: memoryKey, value, category }),
      });
      await get().fetchMemories(port, agentId);
    } catch (error) {
      console.error("Failed to add memory:", error);
    }
  },

  deleteMemory: async (port: number, agentId: string, memoryKey: string) => {
    try {
      await fetch(`http://127.0.0.1:${port}/agents/${agentId}/memories`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ memory_key: memoryKey }),
      });
      await get().fetchMemories(port, agentId);
    } catch (error) {
      console.error("Failed to delete memory:", error);
    }
  },
}));
