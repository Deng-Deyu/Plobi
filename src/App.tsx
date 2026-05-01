import { useState, useEffect } from "react";
import ChatPanel from "./components/layout/ChatPanel";
import Sidebar from "./components/layout/Sidebar";
import AgentRail from "./components/layout/AgentRail";
import TopBar from "./components/layout/TopBar";
import AgentConfigForm from "./components/settings/AgentConfigForm";
import PluginManager from "./components/settings/PluginManager";
import SandboxConfirm from "./components/sandbox/SandboxConfirm";
import { useChatStore } from "./store/chatStore";
import { useStream } from "./hooks/useStream";

export default function App() {
  const currentSession = useChatStore((s) => s.currentSession);
  const sessions = useChatStore((s) => s.sessions);
  const createSession = useChatStore((s) => s.createSession);
  const setCurrentSession = useChatStore((s) => s.setCurrentSession);
  const addMessage = useChatStore((s) => s.addMessage);
  const { startStream } = useStream();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [railCollapsed, setRailCollapsed] = useState(false);
  const [showAgentConfig, setShowAgentConfig] = useState(false);
  const [showPluginManager, setShowPluginManager] = useState(false);
  const [showSandbox, setShowSandbox] = useState(false);

  // Listen for overlay messages
  useEffect(() => {
    let unlisten: (() => void) | undefined;

    const setupListener = async () => {
      const { listen } = await import("@tauri-apps/api/event");
      unlisten = await listen<{ prompt: string }>("overlay-send-message", (event) => {
        const { prompt } = event.payload;

        // Get or create a session
        let session = currentSession;
        if (!session) {
          session = createSession();
        }

        // Add user message to store
        addMessage(session.id, {
          id: crypto.randomUUID(),
          sessionId: session.id,
          agentId: "user",
          role: "user",
          content: prompt,
          streamBuffer: "",
          isStreaming: false,
          attachments: [],
          timestamp: Date.now(),
        });

        // Start streaming from Master Agent
        startStream({
          sessionId: session.id,
          agentId: "master",
          prompt,
        });
      });
    };

    setupListener();

    return () => {
      unlisten?.();
    };
  }, [currentSession, createSession, addMessage, startStream]);

  return (
    <div className="flex h-screen w-screen bg-bg-0 text-text-primary overflow-hidden">
      {/* Sidebar */}
      {!sidebarCollapsed && (
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSession?.id ?? null}
          onSelectSession={setCurrentSession}
          onNewSession={createSession}
          onCollapse={() => setSidebarCollapsed(true)}
        />
      )}

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar
          title={currentSession?.title ?? "Plobi Agent"}
          onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
          onToggleRail={() => setRailCollapsed(!railCollapsed)}
          onOpenPlugins={() => setShowPluginManager(true)}
          onOpenSandbox={() => setShowSandbox(true)}
        />
        <ChatPanel session={currentSession} />
      </div>

      {/* Agent Rail */}
      {!railCollapsed && <AgentRail onCollapse={() => setRailCollapsed(true)} onOpenConfig={() => setShowAgentConfig(true)} onOpenPlugins={() => setShowPluginManager(true)} onOpenSandbox={() => setShowSandbox(true)} />}

      {/* Agent Config Modal */}
      {showAgentConfig && <AgentConfigForm onClose={() => setShowAgentConfig(false)} />}

      {/* Plugin Manager Modal */}
      {showPluginManager && <PluginManager onClose={() => setShowPluginManager(false)} />}

      {/* Sandbox Confirm Modal */}
      {showSandbox && <SandboxConfirm onClose={() => setShowSandbox(false)} />}
    </div>
  );
}
