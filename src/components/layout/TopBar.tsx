import { useSettingsStore } from "../../store/settingsStore";

interface TopBarProps {
  title: string;
  onToggleSidebar: () => void;
  onToggleRail: () => void;
  onOpenPlugins: () => void;
  onOpenSandbox: () => void;
}

export default function TopBar({ title, onToggleSidebar, onToggleRail, onOpenPlugins, onOpenSandbox }: TopBarProps) {
  const theme = useSettingsStore((s) => s.theme);
  const toggleTheme = useSettingsStore((s) => s.toggleTheme);

  return (
    <div className="flex items-center h-12 px-4 border-b border-[var(--border)] bg-[var(--bg-1)] shrink-0">
      <button onClick={onToggleSidebar} className="p-2 rounded-lg hover:bg-[var(--bg-2)] mr-2" title="切换侧边栏">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <span className="text-sm font-semibold flex-1 truncate">{title}</span>
      <div className="flex items-center gap-1">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-[var(--bg-2)] text-[var(--text-secondary)] transition-colors"
          title={theme === "light" ? "切换暗色主题" : "切换亮色主题"}
        >
          {theme === "light" ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>
        <button onClick={onOpenSandbox} className="p-2 rounded-lg hover:bg-[var(--bg-2)] text-[var(--text-secondary)]" title="代码执行">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
          </svg>
        </button>
        <button onClick={onOpenPlugins} className="p-2 rounded-lg hover:bg-[var(--bg-2)] text-[var(--text-secondary)]" title="插件管理">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2l2 7h7l-5.5 4 2 7L12 16l-5.5 4 2-7L3 9h7z" />
          </svg>
        </button>
        <button onClick={onToggleRail} className="p-2 rounded-lg hover:bg-[var(--bg-2)] text-[var(--text-secondary)]" title="切换 Agent 面板">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="18" /><rect x="14" y="3" width="7" height="18" />
          </svg>
        </button>
      </div>
    </div>
  );
}
