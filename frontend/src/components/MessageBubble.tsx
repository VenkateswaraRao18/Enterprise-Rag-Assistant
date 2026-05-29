import type { Message } from "../types";
import { renderSimpleMarkdown } from "../utils/format";

type Props = {
  message: Message;
  onViewCitations?: () => void;
};

export default function MessageBubble({ message: m, onViewCitations }: Props) {
  const isUser = m.role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`avatar ${isUser ? "avatar-user" : "avatar-bot"}`}>
        {isUser ? "You" : "AI"}
      </div>
      <div
        className={[
          "bubble",
          isUser ? "bubble-user" : "bubble-assistant",
          m.securityBlocked ? "bubble-security" : "",
          m.abstained ? "bubble-abstain" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="bubble-header">
          <span className="bubble-name">{isUser ? "You" : "Knowledge Assistant"}</span>
          {m.time && <span className="bubble-time">{m.time}</span>}
        </div>

        <div className="bubble-body">
          {isUser ? m.content : renderSimpleMarkdown(m.content)}
        </div>

        {!isUser && (
          <div className="bubble-footer">
            {m.securityBlocked && (
              <span className="chip chip-warn">
                Security · {m.securityCategory || "blocked"}
              </span>
            )}
            {m.abstained && !m.securityBlocked && (
              <span className="chip chip-warn">Low confidence · limited evidence</span>
            )}
            {m.stats && (
              <span className="chip chip-muted">
                ACL {m.stats.allowed_docs} docs · {m.stats.fused_count} sources
              </span>
            )}
            {m.citations && m.citations.length > 0 && (
              <button type="button" className="chip chip-action" onClick={onViewCitations}>
                View {m.citations.length} citations →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
