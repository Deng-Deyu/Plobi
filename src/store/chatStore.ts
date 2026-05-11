import { create } from "zustand";

// ─── Types ────────────────────────────────────────────────

export interface Attachment {
  id: string;
  type: "image" | "audio" | "document" | "video" | "other";
  name: string;
  size: number;
  path: string;
  mimeType: string;
  preview?: string;
}

export interface Message {
  id: string;
  sessionId: string;
  agentId: string;
  role: "user" | "assistant" | "system";
  content: string;
  streamBuffer: string;
  isStreaming: boolean;
  attachments: Attachment[];
  planId?: string;
  timestamp: number;
}

export interface Session {
  id: string;
  title: string;
  preview: string;
  messages: Message[];
  activeAgents: string[];
  createdAt: number;
  updatedAt: number;
}

// ─── Store ────────────────────────────────────────────────

interface ChatState {
  sessions: Session[];
  currentSession: Session | null;
  isLoadingSessions: boolean;

  // Actions
  loadSessions: (port: number) => Promise<void>;
  loadMessages: (port: number, sessionId: string) => Promise<void>;
  createSession: (port?: number) => Promise<Session>;
  setCurrentSession: (id: string, port?: number) => void;
  addMessage: (sessionId: string, message: Message) => void;
  appendToken: (sessionId: string, messageId: string, token: string) => void;
  setMessageStreaming: (sessionId: string, messageId: string, streaming: boolean) => void;
  updateSessionTitle: (sessionId: string, title: string) => void;
  clearSessions: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSession: null,
  isLoadingSessions: false,

  loadSessions: async (port: number) => {
    set({ isLoadingSessions: true });
    try {
      const res = await fetch(`http://127.0.0.1:${port}/sessions`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const currentState = get();

      const sessions: Session[] = data.map((s: Record<string, unknown>) => {
        const existingSession = currentState.sessions.find((es) => es.id === s.id);
        return {
          id: s.id as string,
          title: s.title as string,
          preview: (s.preview as string) || "",
          // Preserve in-memory messages if this session is already loaded
          messages: existingSession?.messages ?? [],
          activeAgents: (s.active_agent_ids as string[]) || ["master"],
          createdAt: ((s.created_at as number) || 0) * 1000,
          updatedAt: ((s.updated_at as number) || 0) * 1000,
        };
      });

      // Also keep any sessions that exist locally but not on backend yet
      const backendIds = new Set(sessions.map((s) => s.id));
      for (const existing of currentState.sessions) {
        if (!backendIds.has(existing.id)) {
          sessions.push(existing);
        }
      }

      // Update currentSession if its title/preview changed
      const updatedCurrent = currentState.currentSession
        ? sessions.find((s) => s.id === currentState.currentSession!.id) ?? currentState.currentSession
        : null;

      set({ sessions, currentSession: updatedCurrent, isLoadingSessions: false });
    } catch (err) {
      console.error("[ChatStore] Failed to load sessions:", err);
      set({ isLoadingSessions: false });
    }
  },

  loadMessages: async (port: number, sessionId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/sessions/${sessionId}/messages`);
      if (!res.ok) return;
      const data = await res.json();
      const messages: Message[] = data.map((m: Record<string, unknown>) => ({
        id: m.id as string,
        sessionId: m.session_id as string,
        agentId: m.agent_id as string,
        role: m.role as "user" | "assistant" | "system",
        content: m.content as string,
        streamBuffer: "",
        isStreaming: false,
        attachments: (m.attachments as Attachment[]) || [],
        planId: m.plan_id as string | undefined,
        timestamp: ((m.created_at as number) || 0) * 1000,
      }));

      set((s) => ({
        sessions: s.sessions.map((sess) =>
          sess.id === sessionId ? { ...sess, messages } : sess
        ),
        currentSession:
          s.currentSession?.id === sessionId
            ? { ...s.currentSession, messages }
            : s.currentSession,
      }));
    } catch (err) {
      console.error("[ChatStore] Failed to load messages:", err);
    }
  },

  createSession: async (port?: number) => {
    // If port is provided, create session on backend first
    let sessionId = crypto.randomUUID();
    let title = "新对话";

    if (port) {
      try {
        const res = await fetch(`http://127.0.0.1:${port}/sessions`, { method: "POST" });
        if (res.ok) {
          const data = await res.json();
          sessionId = data.id;
          title = data.title;
        }
      } catch (err) {
        console.error("[ChatStore] Failed to create session on backend:", err);
      }
    }

    const session: Session = {
      id: sessionId,
      title,
      preview: "",
      messages: [],
      activeAgents: ["master"],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    set((s) => ({
      sessions: [session, ...s.sessions],
      currentSession: session,
    }));
    return session;
  },

  setCurrentSession: (id: string, port?: number) => {
    const session = get().sessions.find((s) => s.id === id) ?? null;
    set({ currentSession: session });
    // Load messages from backend if session has no messages yet
    if (session && session.messages.length === 0 && port) {
      get().loadMessages(port, id);
    }
  },

  addMessage: (sessionId: string, message: Message) => {
    set((s) => ({
      sessions: s.sessions.map((sess) =>
        sess.id === sessionId
          ? {
              ...sess,
              messages: [...sess.messages, message],
              updatedAt: Date.now(),
              preview: message.content.slice(0, 60),
            }
          : sess
      ),
      currentSession:
        s.currentSession?.id === sessionId
          ? {
              ...s.currentSession,
              messages: [...s.currentSession.messages, message],
              updatedAt: Date.now(),
              preview: message.content.slice(0, 60),
            }
          : s.currentSession,
    }));
  },

  appendToken: (sessionId: string, messageId: string, token: string) => {
    const updateMessages = (messages: Message[]) =>
      messages.map((m) =>
        m.id === messageId
          ? { ...m, streamBuffer: m.streamBuffer + token, content: m.streamBuffer + token }
          : m
      );

    set((s) => ({
      sessions: s.sessions.map((sess) =>
        sess.id === sessionId ? { ...sess, messages: updateMessages(sess.messages) } : sess
      ),
      currentSession:
        s.currentSession?.id === sessionId
          ? { ...s.currentSession, messages: updateMessages(s.currentSession.messages) }
          : s.currentSession,
    }));
  },

  setMessageStreaming: (sessionId: string, messageId: string, streaming: boolean) => {
    const updateMessages = (messages: Message[]) =>
      messages.map((m) => (m.id === messageId ? { ...m, isStreaming: streaming } : m));

    set((s) => ({
      sessions: s.sessions.map((sess) =>
        sess.id === sessionId ? { ...sess, messages: updateMessages(sess.messages) } : sess
      ),
      currentSession:
        s.currentSession?.id === sessionId
          ? { ...s.currentSession, messages: updateMessages(s.currentSession.messages) }
          : s.currentSession,
    }));
  },

  updateSessionTitle: (sessionId: string, title: string) => {
    set((s) => ({
      sessions: s.sessions.map((sess) =>
        sess.id === sessionId ? { ...sess, title } : sess
      ),
      currentSession:
        s.currentSession?.id === sessionId
          ? { ...s.currentSession, title }
          : s.currentSession,
    }));
  },

  clearSessions: () => set({ sessions: [], currentSession: null }),
}));
