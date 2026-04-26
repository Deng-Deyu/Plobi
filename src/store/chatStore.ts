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

  // Actions
  createSession: () => Session;
  setCurrentSession: (id: string) => void;
  addMessage: (sessionId: string, message: Message) => void;
  appendToken: (sessionId: string, messageId: string, token: string) => void;
  setMessageStreaming: (sessionId: string, messageId: string, streaming: boolean) => void;
  clearSessions: () => void;
}

let _sessionCounter = 0;

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSession: null,

  createSession: () => {
    _sessionCounter++;
    const session: Session = {
      id: crypto.randomUUID(),
      title: `新对话 ${_sessionCounter}`,
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

  setCurrentSession: (id: string) => {
    const session = get().sessions.find((s) => s.id === id) ?? null;
    set({ currentSession: session });
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

  clearSessions: () => set({ sessions: [], currentSession: null }),
}));
