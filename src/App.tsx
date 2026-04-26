import { useState } from "react";
import ChatPanel from "./components/layout/ChatPanel";
import Sidebar from "./components/layout/Sidebar";
import AgentRail from "./components/layout/AgentRail";
import TopBar from "./components/layout/TopBar";
import { useChatStore } from "./store/chatStore";

export default function App() {
  const currentSession = useChatStore((s) => s.currentSession);
  const sessions = useChatStore((s) => s.sessions);
  const createSession = useChatStore((s) => s.createSession);
  const setCurrentSession = useChatStore((s) => s.setCurrentSession);

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [railCollapsed, setRailCollapsed] = useState(false);

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
        />
        <ChatPanel session={currentSession} />
      </div>

      {/* Agent Rail */}
      {!railCollapsed && <AgentRail onCollapse={() => setRailCollapsed(true)} />}
    </div>
  );
}
