import { create } from 'zustand';

export interface Plugin {
  id: string;
  name: string;
  type: string;
  package: string;
  enabled: boolean;
}

interface PluginStore {
  plugins: Plugin[];
  setPlugins: (plugins: Plugin[]) => void;
}

export const usePluginStore = create<PluginStore>((set) => ({
  plugins: [],
  setPlugins: (plugins) => set({ plugins }),
}));
