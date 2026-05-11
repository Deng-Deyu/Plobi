import { useEffect, useRef } from "react";
import type { Agent } from "../../store/agentStore";
import AgentAvatar from "./AgentAvatar";
import AgentStatusBadge from "./AgentStatusBadge";
import { X } from "lucide-react";
import { getSkillColor } from "../../lib/skills";
import { getMcpIcon } from "../../lib/mcp";

interface AgentDrawerProps {
  agent: Agent;
  onClose: () => void;
  onOpenConfig: () => void;
}

export default function AgentDrawer({ agent, onClose, onOpenConfig }: AgentDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Close on click outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    // Delay to avoid immediate close from the click that opened it
    const timer = setTimeout(() => {
      document.addEventListener("mousedown", handleClick);
    }, 100);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("mousedown", handleClick);
    };
  }, [onClose]);

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/20 z-40 animate-fade-in" />

      {/* Drawer */}
      <div
        ref={drawerRef}
        className="fixed top-0 right-0 h-full w-[340px] bg-[var(--bg-0)] border-l border-[var(--border)] shadow-2xl z-50 flex flex-col animate-slide-in-right"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b border-[var(--border)] shrink-0">
          <span className="text-sm font-semibold">Agent 详情</span>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[var(--bg-2)] text-[var(--text-muted)] transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Agent Profile */}
        <div className="flex-1 overflow-y-auto">
          <div className="flex flex-col items-center pt-8 pb-6 px-5">
            <AgentAvatar
              name={agent.name}
              avatarType={agent.avatar.type === "image" || agent.avatar.type === "url" ? "image" : "initials"}
              avatarValue={agent.avatar.type === "image" || agent.avatar.type === "url" ? agent.avatar.value : undefined}
              size="lg"
            />
            <h2 className="mt-3 text-lg font-semibold">{agent.name}</h2>
            <div className="mt-1.5">
              <AgentStatusBadge status={agent.status} />
            </div>
          </div>

          {/* Info Cards */}
          <div className="px-5 space-y-3">
            {/* Role */}
            <div className="p-3 rounded-xl bg-[var(--bg-1)] border border-[var(--border)]">
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-1">角色</div>
              <div className="text-sm">{agent.role}</div>
            </div>

            {/* Skills */}
            {agent.skills && agent.skills.length > 0 && (
              <div className="p-3 rounded-xl bg-[var(--bg-1)] border border-[var(--border)]">
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-2">技能</div>
                <div className="flex flex-wrap gap-1.5">
                  {agent.skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-2 py-0.5 rounded-md text-[11px] font-medium text-white"
                      style={{ backgroundColor: getSkillColor(skill) }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* ID */}
            <div className="p-3 rounded-xl bg-[var(--bg-1)] border border-[var(--border)]">
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-1">标识</div>
              <div className="text-sm font-mono text-[var(--text-secondary)]">{agent.id}</div>
            </div>

            {/* MCP Servers */}
            {agent.mcpServers && agent.mcpServers.length > 0 && (
              <div className="p-3 rounded-xl bg-[var(--bg-1)] border border-[var(--border)]">
                <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-2">
                  MCP 服务
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {agent.mcpServers.map((server) => {
                    const McpIcon = getMcpIcon(server);
                    return (
                      <span
                        key={server}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-[var(--accent)]/10 text-[var(--accent)]"
                      >
                        <McpIcon size={10} />
                        {server}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Status Info */}
            <div className="p-3 rounded-xl bg-[var(--bg-1)] border border-[var(--border)]">
              <div className="text-[10px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-1">状态</div>
              <div className="flex items-center gap-2 text-sm">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{
                    backgroundColor:
                      agent.status === "idle"
                        ? "var(--text-muted)"
                        : agent.status === "thinking"
                        ? "var(--running)"
                        : agent.status === "running"
                        ? "var(--warning)"
                        : agent.status === "done"
                        ? "var(--success)"
                        : "var(--error)",
                  }}
                />
                {agent.status === "idle" && "空闲 — 等待任务"}
                {agent.status === "thinking" && "思考中 — 正在生成回复"}
                {agent.status === "running" && "执行中 — 正在运行工具"}
                {agent.status === "done" && "已完成 — 上次任务成功"}
                {agent.status === "error" && "错误 — 需要用户介入"}
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-4 border-t border-[var(--border)] shrink-0 space-y-2">
          <button
            onClick={() => { onOpenConfig(); onClose(); }}
            className="w-full h-9 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent-hover)] transition-colors"
          >
            配置此 Agent
          </button>
          <button
            onClick={onClose}
            className="w-full h-9 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-2)] transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </>
  );
}
