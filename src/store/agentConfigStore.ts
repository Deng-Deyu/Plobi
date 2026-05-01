import { create } from "zustand";

// ─── Types ────────────────────────────────────────────────

export interface AvatarConfig {
  type: "emoji" | "url" | "initials";
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
      const agents: AgentConfig[] = await res.json();
      set({ agents, isLoading: false });
    } catch {
      set({ isLoading: false });
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
