import type { Citation } from "../types";

export function formatTime(date = new Date()) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function sourceLabel(type: string) {
  const map: Record<string, string> = {
    slack: "Slack",
    jira: "Jira",
    kb: "Knowledge Base",
    incident: "Incident",
    oncall: "On-Call",
  };
  return map[type] || type;
}

export function sourceIcon(type: string) {
  const map: Record<string, string> = {
    slack: "💬",
    jira: "🎫",
    kb: "📘",
    incident: "🚨",
    oncall: "📟",
  };
  return map[type] || "📄";
}

export function parseTitle(title: string) {
  const parts = title.split("|").map((p) => p.trim());
  if (parts.length >= 3) {
    return { channel: parts[0], time: parts[1], author: parts[2] };
  }
  return { channel: title, time: "", author: "" };
}

export function renderSimpleMarkdown(text: string) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    const html = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    return (
      <span key={i}>
        <span dangerouslySetInnerHTML={{ __html: html }} />
        {i < lines.length - 1 ? <br /> : null}
      </span>
    );
  });
}

export function groupCitationsByType(citations: Citation[]) {
  const groups: Record<string, Citation[]> = {};
  for (const c of citations) {
    const t = c.source_type || "other";
    if (!groups[t]) groups[t] = [];
    groups[t].push(c);
  }
  return groups;
}
