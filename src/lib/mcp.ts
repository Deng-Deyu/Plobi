import { Search, FolderOpen, Globe, Terminal, Database, Cpu, Package, FileCode } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export function getMcpIcon(name: string): LucideIcon {
  const n = name.toLowerCase();
  if (n.includes("search") || n.includes("brave") || n.includes("bing") || n.includes("google")) {
    return Search;
  }
  if (n.includes("file") || n.includes("fs") || n.includes("folder")) {
    return FolderOpen;
  }
  if (n.includes("fetch") || n.includes("http") || n.includes("web") || n.includes("browser")) {
    return Globe;
  }
  if (n.includes("db") || n.includes("sql") || n.includes("sqlite") || n.includes("postgres")) {
    return Database;
  }
  if (n.includes("shell") || n.includes("cmd") || n.includes("bash")) {
    return Terminal;
  }
  if (n.includes("python") || n.includes("py")) {
    return FileCode;
  }
  if (n.includes("npm") || n.includes("node")) {
    return Package;
  }
  return Cpu;
}
