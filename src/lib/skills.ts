export function getSkillColor(skill: string): string {
  const s = skill.toLowerCase();
  if (s.includes("code") || s.includes("program") || s.includes("dev") || s.includes("script")) {
    return "#3B82F6"; // blue
  }
  if (s.includes("search") || s.includes("web") || s.includes("fetch") || s.includes("brave")) {
    return "#22C55E"; // green
  }
  if (s.includes("audio") || s.includes("music") || s.includes("sound") || s.includes("score")) {
    return "#A855F7"; // purple
  }
  if (s.includes("file") || s.includes("doc") || s.includes("read") || s.includes("write") || s.includes("fs")) {
    return "#F97316"; // orange
  }
  if (s.includes("video") || s.includes("clip") || s.includes("ffmpeg") || s.includes("render")) {
    return "#EF4444"; // red
  }
  if (s.includes("image") || s.includes("photo") || s.includes("vision") || s.includes("paint")) {
    return "#EC4899"; // pink
  }
  return "#6B7280"; // gray
}
