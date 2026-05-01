import { useState, useEffect } from "react";
import { useAgentConfigStore } from "../../store/agentConfigStore";
import { useSettingsStore } from "../../store/settingsStore";

interface AgentConfigFormProps {
  onClose: () => void;
}

export default function AgentConfigForm({ onClose }: AgentConfigFormProps) {
  const backendPort = useSettingsStore((s) => s.backendPort);
  const agents = useAgentConfigStore((s) => s.agents);
  const selectedAgentId = useAgentConfigStore((s) => s.selectedAgentId);
  const memories = useAgentConfigStore((s) => s.memories);
  const fetchAgents = useAgentConfigStore((s) => s.fetchAgents);
  const selectAgent = useAgentConfigStore((s) => s.selectAgent);
  const updateAgent = useAgentConfigStore((s) => s.updateAgent);
  const fetchMemories = useAgentConfigStore((s) => s.fetchMemories);
  const addMemory = useAgentConfigStore((s) => s.addMemory);
  const deleteMemory = useAgentConfigStore((s) => s.deleteMemory);

  const [activeTab, setActiveTab] = useState<"config" | "memory">("config");

  // Memory form state
  const [newMemoryKey, setNewMemoryKey] = useState("");
  const [newMemoryValue, setNewMemoryValue] = useState("");
  const [newMemoryCategory, setNewMemoryCategory] = useState("general");

  // Edit form state
  const [editName, setEditName] = useState("");
  const [editAvatarType, setEditAvatarType] = useState<"emoji" | "url" | "initials">("emoji");
  const [editAvatarValue, setEditAvatarValue] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editTone, setEditTone] = useState("");
  const [editGreeting, setEditGreeting] = useState("");
  const [editProvider, setEditProvider] = useState("deepseek");
  const [editModelId, setEditModelId] = useState("deepseek-chat");
  const [editTemperature, setEditTemperature] = useState(0.7);
  const [editMaxTokens, setEditMaxTokens] = useState(4096);
  const [editSkills, setEditSkills] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAgents(backendPort);
  }, [backendPort, fetchAgents]);

  useEffect(() => {
    if (selectedAgentId) {
      fetchMemories(backendPort, selectedAgentId);
    }
  }, [selectedAgentId, backendPort, fetchMemories]);

  // Populate form when agent is selected
  const selectedAgent = agents.find((a) => a.id === selectedAgentId);
  useEffect(() => {
    if (selectedAgent) {
      setEditName(selectedAgent.name);
      setEditAvatarType(selectedAgent.avatar.type as "emoji" | "url" | "initials");
      setEditAvatarValue(selectedAgent.avatar.value);
      setEditDescription(selectedAgent.persona.description);
      setEditTone(selectedAgent.persona.tone);
      setEditGreeting(selectedAgent.persona.greeting);
      setEditProvider(selectedAgent.model.provider);
      setEditModelId(selectedAgent.model.model_id);
      setEditTemperature(selectedAgent.model.temperature);
      setEditMaxTokens(selectedAgent.model.max_tokens);
      setEditSkills(selectedAgent.skills.join(", "));
    }
  }, [selectedAgent]);

  const handleSave = async () => {
    if (!selectedAgentId) return;
    setSaving(true);
    try {
      await updateAgent(backendPort, selectedAgentId, {
        name: editName,
        avatar: { type: editAvatarType, value: editAvatarValue },
        persona: {
          description: editDescription,
          tone: editTone,
          greeting: editGreeting,
        },
        model: {
          provider: editProvider,
          model_id: editModelId,
          temperature: editTemperature,
          max_tokens: editMaxTokens,
        },
        skills: editSkills
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
    } finally {
      setSaving(false);
    }
  };

  const handleAddMemory = async () => {
    if (!selectedAgentId || !newMemoryKey.trim() || !newMemoryValue.trim()) return;
    await addMemory(backendPort, selectedAgentId, newMemoryKey.trim(), newMemoryValue.trim(), newMemoryCategory);
    setNewMemoryKey("");
    setNewMemoryValue("");
  };

  const handleDeleteMemory = async (memoryKey: string) => {
    if (!selectedAgentId) return;
    await deleteMemory(backendPort, selectedAgentId, memoryKey);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[var(--bg-1)] border border-[var(--border)] rounded-2xl w-[720px] max-h-[80vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <h2 className="text-lg font-semibold">Agent 配置</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-[var(--bg-2)] transition-colors text-[var(--text-muted)]"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex flex-1 min-h-0">
          {/* Agent List */}
          <div className="w-48 border-r border-[var(--border)] overflow-y-auto">
            {agents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => selectAgent(agent.id)}
                className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm text-left transition-colors ${
                  selectedAgentId === agent.id
                    ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                    : "hover:bg-[var(--bg-2)] text-[var(--text-primary)]"
                }`}
              >
                <span className="text-lg">{agent.avatar.value}</span>
                <span className="truncate">{agent.name}</span>
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 flex flex-col min-h-0">
            {selectedAgent ? (
              <>
                {/* Tabs */}
                <div className="flex border-b border-[var(--border)]">
                  <button
                    onClick={() => setActiveTab("config")}
                    className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                      activeTab === "config"
                        ? "text-[var(--accent)] border-b-2 border-[var(--accent)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    }`}
                  >
                    基本配置
                  </button>
                  <button
                    onClick={() => setActiveTab("memory")}
                    className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                      activeTab === "memory"
                        ? "text-[var(--accent)] border-b-2 border-[var(--accent)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    }`}
                  >
                    记忆管理
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-5 space-y-4">
                  {activeTab === "config" ? (
                    <>
                      {/* Name & Avatar */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs text-[var(--text-muted)] mb-1">名称</label>
                          <input
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                          />
                        </div>
                        <div className="flex gap-2">
                          <div className="flex-1">
                            <label className="block text-xs text-[var(--text-muted)] mb-1">头像类型</label>
                            <select
                              value={editAvatarType}
                              onChange={(e) => setEditAvatarType(e.target.value as "emoji" | "url" | "initials")}
                              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                            >
                              <option value="emoji">Emoji</option>
                              <option value="url">URL</option>
                              <option value="initials">首字母</option>
                            </select>
                          </div>
                          <div className="flex-1">
                            <label className="block text-xs text-[var(--text-muted)] mb-1">头像值</label>
                            <input
                              value={editAvatarValue}
                              onChange={(e) => setEditAvatarValue(e.target.value)}
                              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Persona */}
                      <div>
                        <label className="block text-xs text-[var(--text-muted)] mb-1">人格描述</label>
                        <textarea
                          value={editDescription}
                          onChange={(e) => setEditDescription(e.target.value)}
                          rows={2}
                          className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] resize-none focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs text-[var(--text-muted)] mb-1">语气风格</label>
                          <input
                            value={editTone}
                            onChange={(e) => setEditTone(e.target.value)}
                            className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-[var(--text-muted)] mb-1">问候语</label>
                          <input
                            value={editGreeting}
                            onChange={(e) => setEditGreeting(e.target.value)}
                            className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                          />
                        </div>
                      </div>

                      {/* Model */}
                      <div className="p-3 rounded-lg bg-[var(--bg-0)] border border-[var(--border)]">
                        <h3 className="text-xs font-medium text-[var(--text-muted)] mb-2">模型配置</h3>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs text-[var(--text-muted)] mb-1">Provider</label>
                            <select
                              value={editProvider}
                              onChange={(e) => setEditProvider(e.target.value)}
                              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                            >
                              <option value="deepseek">DeepSeek</option>
                              <option value="openai">OpenAI</option>
                              <option value="anthropic">Anthropic</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-xs text-[var(--text-muted)] mb-1">Model ID</label>
                            <input
                              value={editModelId}
                              onChange={(e) => setEditModelId(e.target.value)}
                              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-[var(--text-muted)] mb-1">Temperature: {editTemperature}</label>
                            <input
                              type="range"
                              min="0"
                              max="2"
                              step="0.1"
                              value={editTemperature}
                              onChange={(e) => setEditTemperature(parseFloat(e.target.value))}
                              className="w-full accent-[var(--accent)]"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-[var(--text-muted)] mb-1">Max Tokens</label>
                            <input
                              type="number"
                              value={editMaxTokens}
                              onChange={(e) => setEditMaxTokens(parseInt(e.target.value) || 4096)}
                              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Skills */}
                      <div>
                        <label className="block text-xs text-[var(--text-muted)] mb-1">技能 (逗号分隔)</label>
                        <input
                          value={editSkills}
                          onChange={(e) => setEditSkills(e.target.value)}
                          className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-0)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                        />
                      </div>

                      {/* Save */}
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="w-full py-2.5 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent-hover)] disabled:opacity-40 transition-colors"
                      >
                        {saving ? "保存中..." : "保存配置"}
                      </button>
                    </>
                  ) : (
                    <>
                      {/* Memory List */}
                      {memories.length === 0 ? (
                        <div className="text-center py-8 text-[var(--text-muted)] text-sm">
                          暂无记忆数据
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {memories.map((m) => (
                            <div
                              key={m.key}
                              className="flex items-start gap-3 p-3 rounded-lg bg-[var(--bg-0)] border border-[var(--border)]"
                            >
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-xs font-medium text-[var(--accent)]">{m.memory_key}</span>
                                  <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-2)] text-[var(--text-muted)]">{m.category}</span>
                                </div>
                                <p className="text-sm text-[var(--text-primary)] break-all">{m.value}</p>
                              </div>
                              <button
                                onClick={() => handleDeleteMemory(m.memory_key)}
                                className="p-1 rounded hover:bg-red-500/10 text-[var(--text-muted)] hover:text-red-500 transition-colors shrink-0"
                              >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                </svg>
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Add Memory Form */}
                      <div className="p-3 rounded-lg bg-[var(--bg-0)] border border-[var(--border)] space-y-3">
                        <h3 className="text-xs font-medium text-[var(--text-muted)]">添加记忆</h3>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs text-[var(--text-muted)] mb-1">键名</label>
                            <input
                              value={newMemoryKey}
                              onChange={(e) => setNewMemoryKey(e.target.value)}
                              placeholder="如: user_name"
                              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-[var(--text-muted)] mb-1">分类</label>
                            <select
                              value={newMemoryCategory}
                              onChange={(e) => setNewMemoryCategory(e.target.value)}
                              className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                            >
                              <option value="general">通用</option>
                              <option value="preference">偏好</option>
                              <option value="fact">事实</option>
                              <option value="instruction">指令</option>
                            </select>
                          </div>
                        </div>
                        <div>
                          <label className="block text-xs text-[var(--text-muted)] mb-1">值</label>
                          <input
                            value={newMemoryValue}
                            onChange={(e) => setNewMemoryValue(e.target.value)}
                            placeholder="如: 小明"
                            className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                          />
                        </div>
                        <button
                          onClick={handleAddMemory}
                          disabled={!newMemoryKey.trim() || !newMemoryValue.trim()}
                          className="w-full py-2 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent-hover)] disabled:opacity-40 transition-colors"
                        >
                          添加记忆
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-[var(--text-muted)] text-sm">
                请从左侧选择一个 Agent
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
