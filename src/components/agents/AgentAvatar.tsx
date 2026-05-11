import { useMemo } from "react";

interface AgentAvatarProps {
  name: string;
  avatarType?: "initials" | "image";
  avatarValue?: string; // image path or unused for initials
  size?: "sm" | "md" | "lg";
  isUser?: boolean;
}

// Curated palette — harmonious, premium colors (no plain red/blue/green)
const AVATAR_COLORS = [
  { bg: "#6366F1", text: "#FFFFFF" }, // Indigo
  { bg: "#8B5CF6", text: "#FFFFFF" }, // Violet
  { bg: "#EC4899", text: "#FFFFFF" }, // Pink
  { bg: "#F97316", text: "#FFFFFF" }, // Orange
  { bg: "#14B8A6", text: "#FFFFFF" }, // Teal
  { bg: "#0EA5E9", text: "#FFFFFF" }, // Sky
  { bg: "#A855F7", text: "#FFFFFF" }, // Purple
  { bg: "#F43F5E", text: "#FFFFFF" }, // Rose
  { bg: "#10B981", text: "#FFFFFF" }, // Emerald
  { bg: "#EAB308", text: "#1A1A1A" }, // Yellow
];

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
}

function getInitials(name: string): string {
  // For Chinese names take first char; for English take first letters of first two words
  const trimmed = name.trim();
  if (!trimmed) return "?";

  // Check if name contains CJK characters
  const cjkMatch = trimmed.match(/[\u4e00-\u9fff\u3400-\u4dbf]/);
  if (cjkMatch) {
    return trimmed.charAt(0);
  }

  const parts = trimmed.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return parts[0].substring(0, 2).toUpperCase();
}

const SIZE_MAP = {
  sm: { container: "w-7 h-7", text: "text-[10px]" },
  md: { container: "w-9 h-9", text: "text-xs" },
  lg: { container: "w-14 h-14", text: "text-lg" },
};

export default function AgentAvatar({
  name,
  avatarType = "initials",
  avatarValue,
  size = "md",
  isUser = false,
}: AgentAvatarProps) {
  const colorIndex = useMemo(() => hashString(name) % AVATAR_COLORS.length, [name]);
  const color = isUser
    ? { bg: "var(--accent)", text: "#FFFFFF" }
    : AVATAR_COLORS[colorIndex];
  const initials = useMemo(() => (isUser ? "我" : getInitials(name)), [name, isUser]);
  const sizeClass = SIZE_MAP[size];

  // Image avatar
  if (avatarType === "image" && avatarValue) {
    return (
      <div
        className={`${sizeClass.container} rounded-full overflow-hidden shrink-0 ring-2 ring-[var(--border)]`}
      >
        <img
          src={avatarValue}
          alt={name}
          className="w-full h-full object-cover"
          onError={(e) => {
            // Fallback to initials on image load error
            (e.target as HTMLImageElement).style.display = "none";
            (e.target as HTMLImageElement).parentElement!.classList.add("avatar-fallback");
          }}
        />
      </div>
    );
  }

  // Initials avatar
  return (
    <div
      className={`${sizeClass.container} rounded-full flex items-center justify-center shrink-0 font-semibold select-none ${sizeClass.text}`}
      style={{ backgroundColor: color.bg, color: color.text }}
    >
      {initials}
    </div>
  );
}
