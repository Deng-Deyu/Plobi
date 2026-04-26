import { create } from "zustand";

interface SettingsState {
  theme: "light" | "dark";
  backendPort: number;
  toggleTheme: () => void;
  setBackendPort: (port: number) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  theme: "light",
  backendPort: 52731,

  toggleTheme: () =>
    set((s) => {
      const next = s.theme === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
      return { theme: next };
    }),

  setBackendPort: (port) => set({ backendPort: port }),
}));
