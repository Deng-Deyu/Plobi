import type { AgentStatus } from "../../store/agentStore";

interface AgentStatusBadgeProps {
  status: AgentStatus;
}

const STATUS_CONFIG: Record<AgentStatus, { label: string; color: string }> = {
  idle: { label: "空闲", color: "var(--text-muted)" },
  thinking: { label: "思考中", color: "var(--running)" },
  running: { label: "执行中", color: "var(--warning)" },
  done: { label: "完成", color: "var(--success)" },
  error: { label: "错误", color: "var(--error)" },
};

export default function AgentStatusBadge({ status }: AgentStatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return (
    <span
      className="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
      style={{ color: config.color, background: `${config.color}15` }}
    >
      {config.label}
    </span>
  );
}
