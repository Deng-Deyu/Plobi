import { useCallback } from "react";
import { useChatStore, type Attachment } from "../store/chatStore";
import { useTaskStore } from "../store/taskStore";
import { useSettingsStore } from "../store/settingsStore";

interface StreamEvent {
  type: "token" | "agent_status" | "plan_created" | "agent_progress" | "agent_message" | "file_output" | "done" | "error";
  content?: string;
  agentId?: string;
  status?: string;
  planId?: string;
  planContent?: string;
  filePath?: string;
  message?: string;
}

export function useStream() {
  const addMessage = useChatStore((s) => s.addMessage);
  const appendToken = useChatStore((s) => s.appendToken);
  const setMessageStreaming = useChatStore((s) => s.setMessageStreaming);
  const updateAgentStatus = useTaskStore((s) => s.updateAgentStatus);
  const backendPort = useSettingsStore((s) => s.backendPort);

  const startStream = useCallback(
    async (params: {
      sessionId: string;
      agentId: string;
      prompt: string;
      attachments?: Attachment[];
    }) => {
      const msgId = crypto.randomUUID();

      // Insert empty streaming message placeholder
      addMessage(params.sessionId, {
        id: msgId,
        sessionId: params.sessionId,
        agentId: params.agentId,
        role: "assistant",
        content: "",
        streamBuffer: "",
        isStreaming: true,
        attachments: [],
        timestamp: Date.now(),
      });

      // Establish SSE connection
      const url = new URL(`http://127.0.0.1:${backendPort}/chat/stream`);
      url.searchParams.set("session_id", params.sessionId);
      url.searchParams.set("agent_id", params.agentId);
      url.searchParams.set("message_id", msgId);

      const es = new EventSource(url.toString());

      es.onmessage = (e) => {
        const data: StreamEvent = JSON.parse(e.data);
        switch (data.type) {
          case "token":
            appendToken(params.sessionId, msgId, data.content ?? "");
            break;
          case "agent_status":
            if (data.agentId && data.status) {
              updateAgentStatus(data.agentId, data.status as "pending" | "running" | "done" | "error");
            }
            break;
          case "plan_created":
            // 插入 PlanCard 消息
            addMessage(params.sessionId, {
              id: crypto.randomUUID(),
              sessionId: params.sessionId,
              agentId: "master",
              role: "assistant",
              content: `<PLAN_CARD_DATA>${data.planContent}</PLAN_CARD_DATA>`,
              streamBuffer: "",
              isStreaming: false,
              attachments: [],
              timestamp: Date.now(),
            });
            break;
          case "agent_progress":
            if (data.agentId && data.status) {
              updateAgentStatus(data.agentId, data.status as "pending" | "running" | "done" | "error");
            }
            break;
          case "agent_message":
            if (data.agentId && data.content) {
              addMessage(params.sessionId, {
                id: crypto.randomUUID(),
                sessionId: params.sessionId,
                agentId: data.agentId,
                role: "assistant",
                content: data.content,
                streamBuffer: "",
                isStreaming: false,
                attachments: [],
                timestamp: Date.now(),
              });
            }
            break;
          case "file_output":
            if (data.filePath) {
              addMessage(params.sessionId, {
                id: crypto.randomUUID(),
                sessionId: params.sessionId,
                agentId: data.agentId || "system",
                role: "system",
                content: `[文件已保存] ${data.filePath}`,
                streamBuffer: "",
                isStreaming: false,
                attachments: [],
                timestamp: Date.now(),
              });
            }
            break;
          case "done":
            setMessageStreaming(params.sessionId, msgId, false);
            es.close();
            // Reload sessions to pick up auto-updated title from backend
            useChatStore.getState().loadSessions(backendPort);
            break;
          case "error":
            setMessageStreaming(params.sessionId, msgId, false);
            es.close();
            break;
        }
      };

      es.onerror = () => {
        setMessageStreaming(params.sessionId, msgId, false);
        es.close();
      };

      // POST the message content (including attachment references)
      await fetch(`http://127.0.0.1:${backendPort}/chat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: params.sessionId,
          agent_id: params.agentId,
          message_id: msgId,
          prompt: params.prompt,
          attachment_ids: params.attachments?.map((a) => a.id) ?? [],
        }),
      });
    },
    [addMessage, appendToken, setMessageStreaming, updateAgentStatus, backendPort]
  );

  return { startStream };
}
