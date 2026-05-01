interface TopBarProps {
  title: string;
  onToggleSidebar: () => void;
  onToggleRail: () => void;
  onOpenPlugins: () => void;
  onOpenSandbox: () => void;
}

export default function TopBar({ title, onToggleSidebar, onToggleRail, onOpenPlugins, onOpenSandbox }: TopBarProps) {
  return (
    <div className="flex items-center h-12 px-4 border-b border-[var(--border)] bg-[var(--bg-1)] shrink-0">
      <button onClick={onToggleSidebar} className="p-2 rounded-lg hover:bg-[var(--bg-2)] mr-2">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <span className="text-sm font-semibold flex-1 truncate">{title}</span>
      <div className="flex items-center gap-2">
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
        <button onClick={onToggleRail} className="p-2 rounded-lg hover:bg-[var(--bg-2)] text-[var(--text-secondary)]">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="18" /><rect x="14" y="3" width="7" height="18" />
          </svg>
        </button>
      </div>
    </div>
  );
}
