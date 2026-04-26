import { create } from "zustand";

export interface TaskState {
  planId: string;
  agentId: string;
  title: string;
  status: "pending" | "waiting" | "running" | "done" | "error";
  summary: string;
  outputFiles: string[];
}

interface TaskStoreState {
  tasks: TaskState[];
  updateAgentStatus: (agentId: string, status: TaskState["status"]) => void;
  addTask: (task: TaskState) => void;
  clearTasks: () => void;
}

export const useTaskStore = create<TaskStoreState>((set) => ({
  tasks: [],

  updateAgentStatus: (agentId, status) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.agentId === agentId ? { ...t, status } : t)),
    })),

  addTask: (task) => set((s) => ({ tasks: [...s.tasks, task] })),

  clearTasks: () => set({ tasks: [] }),
}));
