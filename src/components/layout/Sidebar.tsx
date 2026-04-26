import type { Session } from "../../store/chatStore";
import { formatDateLabel } from "../../lib/formatters";

interface SidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onCollapse: () => void;
}

export default function Sidebar({ sessions, currentSessionId, onSelectSession, onNewSession, onCollapse }: SidebarProps) {
  // Group sessions by date label
  const groups: Record<string, Session[]> = {};
  for (const s of sessions) {
    const label = formatDateLabel(s.updatedAt);
    if (!groups[label]) groups[label] = [];
    groups[label].push(s);
  }

  return (
    <div className="w-[220px] h-full flex flex-col bg-[var(--bg-1)] border-r border-[var(--border)] shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 h-12 border-b border-[var(--border)]">
        <span className="text-sm font-semibold">Plobi Agent</span>
        <button onClick={onCollapse} className="p-1 rounded hover:bg-[var(--bg-2)]">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-2">
        {Object.entries(groups).map(([label, items]) => (
          <div key={label}>
            <div className="px-4 py-1 text-xs text-[var(--text-muted)] font-medium">{label}</div>
            {items.map((s) => (
              <button
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className={`w-full text-left px-4 h-[44px] flex items-center gap-2 text-sm hover:bg-[var(--bg-2)] transition-colors ${
                  s.id === currentSessionId ? "border-l-2 border-[var(--accent)] bg-[var(--accent-muted)]" : ""
                }`}
              >
                <span className="truncate">{s.title}</span>
              </button>
            ))}
          </div>
        ))}
      </div>

      {/* New session */}
      <div className="p-3 border-t border-[var(--border)]">
        <button
          onClick={onNewSession}
          className="w-full h-9 rounded-lg border border-dashed border-[var(--border-strong)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-2)] hover:border-[var(--accent)] transition-colors"
        >
          + 新建对话
        </button>
      </div>
    </div>
  );
}
