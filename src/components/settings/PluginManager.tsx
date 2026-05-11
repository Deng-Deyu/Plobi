import { useState, useEffect } from "react";
import { useSettingsStore } from "../../store/settingsStore";
import { X, Trash2, Package, Terminal, FileCode } from "lucide-react";

interface Plugin {
  id: string;
  name: string;
  type: string;
  description: string;
  enabled: boolean;
  command?: string;
  args?: string[];
  installed_at?: string;
}

interface PluginManagerProps {
  onClose: () => void;
}

export default function PluginManager({ onClose }: PluginManagerProps) {
  const backendPort = useSettingsStore((s) => s.backendPort);
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Install form state
  const [installType, setInstallType] = useState<"npm" | "local">("npm");
  const [showInstall, setShowInstall] = useState(false);
  const [npmPackage, setNpmPackage] = useState("");
  const [npmDesc, setNpmDesc] = useState("");
  const [installing, setInstalling] = useState(false);

  // Local plugin form
  const [localId, setLocalId] = useState("");
  const [localName, setLocalName] = useState("");
  const [localDesc, setLocalDesc] = useState("");
  const [localType, setLocalType] = useState("python");
  const [localCommand, setLocalCommand] = useState("");

  const fetchPlugins = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:${backendPort}/plugins`);
      const data = await res.json();
      setPlugins(Array.isArray(data) ? data : []);
    } catch {
      setPlugins([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, [backendPort]);

  const handleToggle = async (pluginId: string) => {
    try {
      await fetch(`http://127.0.0.1:${backendPort}/plugins/${pluginId}/toggle`, {
        method: "PUT",
      });
      await fetchPlugins();
    } catch (error) {
      console.error("Failed to toggle plugin:", error);
    }
  };

  const handleUninstall = async (pluginId: string) => {
    if (!confirm(`确定要卸载插件 "${pluginId}" 吗？`)) return;
    try {
      await fetch(`http://127.0.0.1:${backendPort}/plugins/${pluginId}`, {
        method: "DELETE",
      });
      await fetchPlugins();
    } catch (error) {
      console.error("Failed to uninstall plugin:", error);
    }
  };

  const handleInstallNpm = async () => {
    if (!npmPackage.trim()) return;
    setInstalling(true);
    try {
      await fetch(`http://127.0.0.1:${backendPort}/plugins/install/npm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ package_name: npmPackage.trim(), description: npmDesc }),
      });
      await fetchPlugins();
      setShowInstall(false);
      setNpmPackage("");
      setNpmDesc("");
    } catch (error) {
      console.error("Failed to install npm plugin:", error);
    } finally {
      setInstalling(false);
    }
  };

  const handleInstallLocal = async () => {
    if (!localId.trim() || !localName.trim()) return;
    setInstalling(true);
    try {
      await fetch(`http://127.0.0.1:${backendPort}/plugins/install/local`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plugin_id: localId.trim(),
          name: localName.trim(),
          description: localDesc,
          plugin_type: localType,
          command: localCommand,
        }),
      });
      await fetchPlugins();
      setShowInstall(false);
      setLocalId("");
      setLocalName("");
      setLocalDesc("");
      setLocalCommand("");
    } catch (error) {
      console.error("Failed to install local plugin:", error);
    } finally {
      setInstalling(false);
    }
  };

  const typeLabel: Record<string, string> = {
    mcp_npm: "MCP (NPM)",
    mcp_local: "MCP (本地)",
    python: "Python",
  };

  const typeIcon: Record<string, React.ReactNode> = {
    mcp_npm: <Package size={14} />,
    mcp_local: <Terminal size={14} />,
    python: <FileCode size={14} />,
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[var(--bg-1)] border border-[var(--border)] rounded-2xl w-[600px] max-h-[70vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <h2 className="text-lg font-semibold">插件管理</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowInstall(!showInstall)}
              className="px-3 py-1.5 rounded-lg bg-[var(--accent)] text-white text-xs font-medium hover:bg-[var(--accent-hover)] transition-colors"
            >
              安装插件
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-[var(--bg-2)] transition-colors text-[var(--text-muted)]"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Install Form */}
        {showInstall && (
          <div className="px-6 py-4 border-b border-[var(--border)] bg-[var(--bg-0)]">
            <div className="flex gap-2 mb-3">
              <button
                onClick={() => setInstallType("npm")}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  installType === "npm" ? "bg-[var(--accent)] text-white" : "bg-[var(--bg-2)] text-[var(--text-muted)]"
                }`}
              >
                NPM 插件
              </button>
              <button
                onClick={() => setInstallType("local")}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  installType === "local" ? "bg-[var(--accent)] text-white" : "bg-[var(--bg-2)] text-[var(--text-muted)]"
                }`}
              >
                本地插件
              </button>
            </div>

            {installType === "npm" ? (
              <div className="space-y-2">
                <input
                  value={npmPackage}
                  onChange={(e) => setNpmPackage(e.target.value)}
                  placeholder="NPM 包名 (如 @anthropic/mcp-server)"
                  className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                />
                <input
                  value={npmDesc}
                  onChange={(e) => setNpmDesc(e.target.value)}
                  placeholder="描述 (可选)"
                  className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                />
                <button
                  onClick={handleInstallNpm}
                  disabled={installing || !npmPackage.trim()}
                  className="w-full py-2 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent-hover)] disabled:opacity-40 transition-colors"
                >
                  {installing ? "安装中..." : "安装 NPM 插件"}
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <input
                    value={localId}
                    onChange={(e) => setLocalId(e.target.value)}
                    placeholder="插件 ID"
                    className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                  />
                  <input
                    value={localName}
                    onChange={(e) => setLocalName(e.target.value)}
                    placeholder="插件名称"
                    className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                  />
                </div>
                <input
                  value={localDesc}
                  onChange={(e) => setLocalDesc(e.target.value)}
                  placeholder="描述 (可选)"
                  className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                />
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={localType}
                    onChange={(e) => setLocalType(e.target.value)}
                    className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                  >
                    <option value="python">Python</option>
                    <option value="mcp_local">MCP (本地)</option>
                  </select>
                  <input
                    value={localCommand}
                    onChange={(e) => setLocalCommand(e.target.value)}
                    placeholder="启动命令"
                    className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm bg-[var(--bg-1)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                  />
                </div>
                <button
                  onClick={handleInstallLocal}
                  disabled={installing || !localId.trim() || !localName.trim()}
                  className="w-full py-2 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent-hover)] disabled:opacity-40 transition-colors"
                >
                  {installing ? "安装中..." : "安装本地插件"}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Plugin List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading ? (
            <div className="text-center py-8 text-[var(--text-muted)] text-sm">加载中...</div>
          ) : plugins.length === 0 ? (
            <div className="text-center py-8 text-[var(--text-muted)] text-sm">
              暂无已安装插件，点击上方"安装插件"添加
            </div>
          ) : (
            plugins.map((plugin) => (
              <div
                key={plugin.id}
                className="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-0)] border border-[var(--border)]"
              >
                <div className="w-8 h-8 rounded-lg bg-[var(--bg-2)] flex items-center justify-center text-[var(--text-muted)] shrink-0">
                  {typeIcon[plugin.type] || <Package size={14} />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium truncate">{plugin.name}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-2)] text-[var(--text-muted)]">
                      {typeLabel[plugin.type] || plugin.type}
                    </span>
                  </div>
                  {plugin.description && (
                    <p className="text-xs text-[var(--text-muted)] truncate">{plugin.description}</p>
                  )}
                </div>

                {/* Toggle */}
                <button
                  onClick={() => handleToggle(plugin.id)}
                  className={`relative w-10 h-5 rounded-full transition-colors shrink-0 ${
                    plugin.enabled ? "bg-[var(--accent)]" : "bg-[var(--bg-2)]"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      plugin.enabled ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>

                {/* Uninstall */}
                <button
                  onClick={() => handleUninstall(plugin.id)}
                  className="p-1.5 rounded hover:bg-red-500/10 text-[var(--text-muted)] hover:text-red-500 transition-colors shrink-0"
                  title="卸载"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
