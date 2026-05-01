import { useState, useEffect, useCallback } from "react";
import { useSettingsStore } from "../../store/settingsStore";

interface SandboxProposal {
  execution_id: string;
  code: string;
  language: string;
  description: string;
  status: string;
}

interface SandboxConfirmProps {
  onClose: () => void;
}

export default function SandboxConfirm({ onClose }: SandboxConfirmProps) {
  const backendPort = useSettingsStore((s) => s.backendPort);
  const [pending, setPending] = useState<SandboxProposal[]>([]);
  const [results, setResults] = useState<Record<string, { stdout: string; stderr: string; exit_code: number }>>({});
  const [executing, setExecuting] = useState<string | null>(null);

  const fetchPending = useCallback(async () => {
    try {
      const res = await fetch(`http://127.0.0.1:${backendPort}/sandbox/pending`);
      const data: SandboxProposal[] = await res.json();
      setPending(data);
    } catch {
      setPending([]);
    }
  }, [backendPort]);

  useEffect(() => {
    fetchPending();
    const interval = setInterval(fetchPending, 3000);
    return () => clearInterval(interval);
  }, [fetchPending]);

  const handleConfirm = async (executionId: string, approved: boolean) => {
    setExecuting(executionId);
    try {
      const res = await fetch(`http://127.0.0.1:${backendPort}/sandbox/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ execution_id: executionId, approved }),
      });
      const data = await res.json();

      if (approved && data.result) {
        setResults((prev) => ({ ...prev, [executionId]: data.result }));
      }

      // Remove from pending
      setPending((prev) => prev.filter((p) => p.execution_id !== executionId));
    } catch (error) {
      console.error("Sandbox confirm error:", error);
    } finally {
      setExecuting(null);
    }
  };

  const langLabel: Record<string, string> = {
    python: "Python",
    shell: "Shell",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[var(--bg-1)] border border-[var(--border)] rounded-2xl w-[640px] max-h-[70vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <h2 className="text-lg font-semibold">代码执行确认</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-[var(--bg-2)] transition-colors text-[var(--text-muted)]"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {pending.length === 0 && Object.keys(results).length === 0 ? (
            <div className="text-center py-8 text-[var(--text-muted)] text-sm">
              暂无待确认的代码执行请求
            </div>
          ) : null}

          {/* Pending executions */}
          {pending.map((proposal) => (
            <div
              key={proposal.execution_id}
              className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 overflow-hidden"
            >
              <div className="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 border-b border-yellow-500/20">
                <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400 font-medium">
                  待确认
                </span>
                <span className="text-xs text-[var(--text-muted)]">
                  {langLabel[proposal.language] || proposal.language}
                </span>
                {proposal.description && (
                  <span className="text-xs text-[var(--text-secondary)] truncate flex-1">
                    {proposal.description}
                  </span>
                )}
              </div>
              <pre className="px-4 py-3 text-sm font-mono overflow-x-auto text-[var(--text-primary)] bg-[var(--bg-0)] max-h-[200px] overflow-y-auto">
                <code>{proposal.code}</code>
              </pre>
              <div className="flex gap-2 px-4 py-3 bg-[var(--bg-0)]">
                <button
                  onClick={() => handleConfirm(proposal.execution_id, true)}
                  disabled={executing === proposal.execution_id}
                  className="flex-1 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 disabled:opacity-40 transition-colors"
                >
                  {executing === proposal.execution_id ? "执行中..." : "确认执行"}
                </button>
                <button
                  onClick={() => handleConfirm(proposal.execution_id, false)}
                  disabled={executing === proposal.execution_id}
                  className="flex-1 py-2 rounded-lg bg-red-600/80 text-white text-sm font-medium hover:bg-red-600 disabled:opacity-40 transition-colors"
                >
                  拒绝
                </button>
              </div>
            </div>
          ))}

          {/* Completed results */}
          {Object.entries(results).map(([execId, result]) => (
            <div
              key={execId}
              className={`rounded-lg border overflow-hidden ${
                result.exit_code === 0
                  ? "border-green-500/30 bg-green-500/5"
                  : "border-red-500/30 bg-red-500/5"
              }`}
            >
              <div className={`flex items-center gap-2 px-4 py-2 border-b ${
                result.exit_code === 0
                  ? "bg-green-500/10 border-green-500/20"
                  : "bg-red-500/10 border-red-500/20"
              }`}>
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                  result.exit_code === 0
                    ? "bg-green-500/20 text-green-400"
                    : "bg-red-500/20 text-red-400"
                }`}>
                  {result.exit_code === 0 ? "执行成功" : `执行失败 (exit: ${result.exit_code})`}
                </span>
              </div>
              {result.stdout && (
                <div className="px-4 py-2">
                  <span className="text-xs text-[var(--text-muted)]">输出：</span>
                  <pre className="text-sm font-mono text-[var(--text-primary)] whitespace-pre-wrap mt-1 max-h-[120px] overflow-y-auto">
                    {result.stdout}
                  </pre>
                </div>
              )}
              {result.stderr && (
                <div className="px-4 py-2 border-t border-[var(--border)]">
                  <span className="text-xs text-red-400">错误：</span>
                  <pre className="text-sm font-mono text-red-400 whitespace-pre-wrap mt-1 max-h-[80px] overflow-y-auto">
                    {result.stderr}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
