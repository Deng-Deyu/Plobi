import { useState, useEffect, type ReactNode } from "react";
import type { Message } from "../../store/chatStore";
import { useAgentStore } from "../../store/agentStore";
import AgentAvatar from "../agents/AgentAvatar";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import PlanCard from "./PlanCard";
import { createHighlighter, type Highlighter } from "shiki";
import { invoke } from "@tauri-apps/api/core";
import { FileText } from "lucide-react";

let globalHighlighter: Highlighter | null = null;
const initShiki = async () => {
  if (!globalHighlighter) {
    globalHighlighter = await createHighlighter({
      themes: ["vitesse-dark", "vitesse-light"],
      langs: ["javascript", "typescript", "python", "json", "bash", "markdown", "html", "css", "cpp", "rust", "xml", "yaml", "toml", "sh"]
    });
  }
  return globalHighlighter as Highlighter;
};

/**
 * Recursively extract plain text from React children.
 */
function extractText(node: ReactNode): string {
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (node == null || typeof node === "boolean") return "";
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (typeof node === "object" && "props" in node) {
    return extractText((node as React.ReactElement).props.children);
  }
  return "";
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const agents = useAgentStore((s) => s.agents);
  const isUser = message.role === "user";
  const agent = isUser ? undefined : agents.find((a) => a.id === message.agentId);

  const displayContent = message.isStreaming ? message.streamBuffer : message.content;

  // File output system message
  const isFileOutput = message.role === "system" && displayContent.startsWith("[文件已保存] ");

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <AgentAvatar
        name={isUser ? "用户" : agent?.name ?? "Agent"}
        avatarType={
          !isUser && agent?.avatar.type === "image" ? "image" : "initials"
        }
        avatarValue={
          !isUser && agent?.avatar.type === "image" ? agent.avatar.value : undefined
        }
        size="sm"
        isUser={isUser}
      />
      <div
        className={`max-w-[70%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}
      >
        {!isUser && !isFileOutput && (
          <span className="text-xs text-[var(--text-secondary)] font-medium">
            {agent?.name ?? "Agent"}
          </span>
        )}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-[var(--accent-muted)] rounded-tr-sm"
              : isFileOutput
              ? "bg-[var(--success)]/10 border border-[var(--success)]/20 rounded-lg"
              : "bg-[var(--bg-0)] border border-[var(--border)] rounded-tl-sm"
          }`}
        >
          {isFileOutput ? (
            <button
              onClick={() => {
                const path = displayContent.replace("[文件已保存] ", "").trim();
                invoke("open_file", { path }).catch(console.error);
              }}
              className="flex items-center gap-2 text-[var(--success)] hover:underline"
            >
              <FileText size={14} />
              <span>{displayContent.replace("[文件已保存] ", "").trim()}</span>
            </button>
          ) : displayContent.startsWith("<PLAN_CARD_DATA>") && displayContent.endsWith("</PLAN_CARD_DATA>") ? (
            <PlanCard planContent={displayContent.replace("<PLAN_CARD_DATA>", "").replace("</PLAN_CARD_DATA>", "")} />
          ) : displayContent ? (
            <div className="markdown-body">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  // Code blocks with language label + copy button
                  pre: ({ children, ...props }) => (
                    <pre
                      className="rounded-lg overflow-x-auto text-sm my-2 p-0 bg-[#121212]"
                      {...props}
                    >
                      {children}
                    </pre>
                  ),
                  code: ({ className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || "");
                    const isBlock = match || (className && className.includes("language-"));
                    
                    if (isBlock) {
                      const lang = match ? match[1] : className?.replace("language-", "").trim();
                      return (
                        <CodeBlockWrapper language={lang ?? ""}>
                          {children}
                        </CodeBlockWrapper>
                      );
                    }
                    // Inline code
                    return (
                      <code
                        className="px-1.5 py-0.5 rounded bg-[var(--bg-2)] font-mono text-[13px]"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  // Tables
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-2">
                      <table className="min-w-full text-sm border-collapse">{children}</table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-[var(--border)] px-3 py-1.5 bg-[var(--bg-2)] text-left font-medium text-xs">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-[var(--border)] px-3 py-1.5 text-xs">
                      {children}
                    </td>
                  ),
                  // Links
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener" className="text-[var(--accent)] hover:underline">
                      {children}
                    </a>
                  ),
                  // Blockquotes
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-3 border-[var(--accent)] pl-3 my-2 text-[var(--text-secondary)] italic">
                      {children}
                    </blockquote>
                  ),
                  // Lists
                  ul: ({ children }) => <ul className="list-disc pl-5 my-1 space-y-0.5">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-5 my-1 space-y-0.5">{children}</ol>,
                  // Paragraphs
                  p: ({ children }) => <p className="my-1.5 leading-relaxed">{children}</p>,
                }}
              >
                {displayContent}
              </ReactMarkdown>
              {message.isStreaming && <span className="streaming-cursor" />}
            </div>
          ) : (
            message.isStreaming && <span className="streaming-cursor" />
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * CodeBlockWrapper — wraps a code block with a header bar (language label + copy).
 * Uses Shiki for asynchronous high-quality syntax highlighting.
 */
function CodeBlockWrapper({ language, children }: { language: string; children: ReactNode }) {
  const [copied, setCopied] = useState(false);
  const [html, setHtml] = useState<string | null>(null);
  
  // Extract the raw code text once
  const codeText = extractText(children).trimEnd();

  useEffect(() => {
    let isMounted = true;
    initShiki().then((hl) => {
      if (!isMounted) return;
      try {
        const highlightedHtml = hl.codeToHtml(codeText, {
          lang: language || "text",
          theme: "vitesse-dark",
        });
        setHtml(highlightedHtml);
      } catch (err) {
        console.error("Shiki highlight error:", err);
        // Fallback to basic if language is unsupported
        const fallbackHtml = hl.codeToHtml(codeText, {
          lang: "text",
          theme: "vitesse-dark",
        });
        setHtml(fallbackHtml);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [codeText, language]);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="relative group">
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#2d2d2d] text-[11px] text-[#999] border-b border-[#3a3a3a]">
        <span className="font-mono">{language || "text"}</span>
        <button
          onClick={handleCopy}
          className="px-2 py-0.5 rounded text-[10px] hover:bg-white/10 transition-colors flex items-center gap-1"
        >
          {copied ? (
            <>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span className="text-[#22C55E]">已复制</span>
            </>
          ) : (
            <>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              复制
            </>
          )}
        </button>
      </div>
      <div className="p-4 overflow-x-auto text-[13px] leading-relaxed shiki-container">
        {html ? (
          <div dangerouslySetInnerHTML={{ __html: html }} />
        ) : (
          <pre><code>{codeText}</code></pre>
        )}
      </div>
    </div>
  );
}
