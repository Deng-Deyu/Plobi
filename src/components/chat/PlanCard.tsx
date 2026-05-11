import { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";

interface PlanCardProps {
  planContent: string;
}

interface ParsedTask {
  title: string;
  agentName: string;
  agentId: string;
  description: string;
  status: string;
}

export default function PlanCard({ planContent }: PlanCardProps) {
  const [expanded, setExpanded] = useState(true);

  // Simple parser for the standardized plan.md format
  const parsedData = useMemo(() => {
    try {
      const titleMatch = planContent.match(/# Plan:\s*(.*)/);
      const title = titleMatch ? titleMatch[1].trim() : "执行计划";

      const statusMatch = planContent.match(/\*\*状态\*\*:\s*(\w+)/);
      const globalStatus = statusMatch ? statusMatch[1].trim() : "dispatching";

      // Split tasks
      const tasks: ParsedTask[] = [];
      const taskBlocks = planContent.split(/### 任务 \d+ — /).slice(1);
      
      for (const block of taskBlocks) {
        const lines = block.split("\n");
        const agentName = lines[0].trim();
        
        let agentId = "";
        let description = "";
        let status = "pending";

        for (const line of lines) {
          if (line.startsWith("**负责 Agent**:")) agentId = line.replace("**负责 Agent**:", "").trim();
          if (line.startsWith("**任务描述**:")) description = line.replace("**任务描述**:", "").trim();
          if (line.startsWith("**状态**:")) status = line.replace("**状态**:", "").trim();
        }

        tasks.push({
          title: `任务 - ${agentName}`,
          agentName,
          agentId,
          description,
          status,
        });
      }

      return { title, globalStatus, tasks };
    } catch (err) {
      console.error("Failed to parse plan.md", err);
      return { title: "执行计划", globalStatus: "error", tasks: [] };
    }
  }, [planContent]);

  const { title, globalStatus, tasks } = parsedData;

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "done": return "text-green-500 bg-green-500/10 border-green-500/20";
      case "running": return "text-blue-500 bg-blue-500/10 border-blue-500/20";
      case "error": return "text-red-500 bg-red-500/10 border-red-500/20";
      default: return "text-gray-400 bg-gray-500/10 border-gray-500/20";
    }
  };

  const getStatusText = (status: string) => {
    switch (status.toLowerCase()) {
      case "done": return "完成";
      case "running": return "执行中...";
      case "pending": return "等待中";
      case "error": return "失败";
      default: return status;
    }
  };

  return (
    <div className="w-full max-w-2xl bg-[var(--bg-1)] border border-[var(--border)] rounded-lg shadow-sm overflow-hidden my-2">
      <div 
        className="px-4 py-3 bg-[var(--bg-2)] border-b border-[var(--border)] flex justify-between items-center cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--accent)]">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          <span className="font-semibold text-sm">{title}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[var(--text-secondary)]">状态: {globalStatus}</span>
          <svg 
            width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </div>
      
      {expanded && (
        <div className="p-4 flex flex-col gap-3">
          {tasks.length > 0 ? (
            tasks.map((task, idx) => (
              <div key={idx} className="bg-[var(--bg-0)] p-3 rounded-md border border-[var(--border)] flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-sm flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[var(--bg-2)] flex items-center justify-center text-xs">
                      {idx + 1}
                    </span>
                    {task.agentName}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs border ${getStatusColor(task.status)}`}>
                    {getStatusText(task.status)}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed pl-7">
                  {task.description}
                </p>
              </div>
            ))
          ) : (
            <div className="text-sm text-[var(--text-secondary)]">
              {/* 如果无法解析成标准化卡片，退化为普通 markdown 渲染 */}
              <div className="markdown-body">
                <ReactMarkdown>{planContent}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
