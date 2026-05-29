import { useCallback, useEffect, useRef, useState } from "react";
import { askQuestion, checkHealth, fetchExampleQueries, fetchPersonas } from "./api";
import MessageBubble from "./components/MessageBubble";
import Sidebar from "./components/Sidebar";
import SourcesPanel from "./components/SourcesPanel";
import type { Message, Persona } from "./types";
import { formatTime } from "./utils/format";

function uid() {
  return Math.random().toString(36).slice(2);
}

export default function App() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personaIdx, setPersonaIdx] = useState(0);
  const [examples, setExamples] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [activeCitations, setActiveCitations] = useState<Message["citations"]>([]);
  const messagesRef = useRef<HTMLDivElement>(null);
  const stickToBottomRef = useRef(true);

  const persona = personas[personaIdx];

  const isNearBottom = useCallback(() => {
    const el = messagesRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }, []);

  const scrollMessagesToBottom = useCallback((force = false) => {
    const el = messagesRef.current;
    if (!el || (!force && !stickToBottomRef.current)) return;
    el.scrollTop = el.scrollHeight;
  }, []);

  const handleMessagesScroll = useCallback(() => {
    stickToBottomRef.current = isNearBottom();
  }, [isNearBottom]);

  useEffect(() => {
    (async () => {
      try {
        const [p, e, ok] = await Promise.all([
          fetchPersonas(),
          fetchExampleQueries(),
          checkHealth(),
        ]);
        setPersonas(p);
        setExamples(e);
        setApiOk(ok);
      } catch {
        setApiOk(false);
      }
    })();
  }, []);

  useEffect(() => {
    scrollMessagesToBottom();
  }, [messages, loading, scrollMessagesToBottom]);

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || !persona || loading) return;
      setError(null);
      setLoading(true);
      stickToBottomRef.current = true;
      const userMsg: Message = {
        id: uid(),
        role: "user",
        content: text.trim(),
        time: formatTime(),
      };
      setMessages((m) => [...m, userMsg]);
      setInput("");
      requestAnimationFrame(() => scrollMessagesToBottom(true));

      try {
        const res = await askQuestion({
          query: text.trim(),
          team: persona.team,
          role: persona.role,
          clearance: persona.clearance,
          top_k: 6,
        });
        const assistantMsg: Message = {
          id: uid(),
          role: "assistant",
          content: res.answer,
          time: formatTime(),
          abstained: res.abstained,
          citations: res.citations,
          stats: res.stats,
          securityBlocked: res.security_blocked,
          securityCategory: res.security_category,
        };
        setMessages((m) => [...m, assistantMsg]);
        setActiveCitations(res.citations);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Request failed");
      } finally {
        setLoading(false);
      }
    },
    [persona, loading, scrollMessagesToBottom]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <div className="logo">
            <span className="logo-icon" />
            <div>
              <h1>TechCorp Knowledge</h1>
              <p>Internal operations assistant</p>
            </div>
          </div>
          <span className="env-badge">Internal · Dev</span>
        </div>
        <div className="topbar-right">
          <div className={`status ${apiOk === true ? "ok" : apiOk === false ? "err" : ""}`}>
            <span className="status-dot" />
            {apiOk === null ? "Connecting…" : apiOk ? "Systems operational" : "API unavailable"}
          </div>
        </div>
      </header>

      <div className="workspace">
        <Sidebar
          personas={personas}
          personaIdx={personaIdx}
          onPersonaChange={setPersonaIdx}
          examples={examples}
          onExample={send}
          onClearChat={() => {
            setMessages([]);
            setActiveCitations([]);
            setError(null);
          }}
        />

        <main className="panel chat-panel">
          <div className="chat-toolbar">
            <div>
              <h2>Assistant</h2>
              <p>Hybrid RAG over Slack, Jira, runbooks, and incidents</p>
            </div>
          </div>

          <div className="messages" ref={messagesRef} onScroll={handleMessagesScroll}>
            {messages.length === 0 && !loading && (
              <div className="welcome">
                <div className="welcome-icon">◇</div>
                <h3>Ask your internal knowledge base</h3>
                <p>
                  Responses are permission-aware and grounded in retrieved evidence with
                  citations.
                </p>
                <div className="welcome-grid">
                  <div className="welcome-card">
                    <strong>Incidents</strong>
                    <span>Root cause, mitigation, SEV status</span>
                  </div>
                  <div className="welcome-card">
                    <strong>Tickets</strong>
                    <span>P1/P0 issues, blocked deploys</span>
                  </div>
                  <div className="welcome-card">
                    <strong>Policies</strong>
                    <span>On-call, escalation, runbooks</span>
                  </div>
                </div>
              </div>
            )}

            {messages.map((m) => (
              <MessageBubble
                key={m.id}
                message={m}
                onViewCitations={() => setActiveCitations(m.citations)}
              />
            ))}

            {loading && (
              <div className="message-row assistant">
                <div className="avatar avatar-bot">AI</div>
                <div className="bubble bubble-assistant loading-bubble">
                  <div className="bubble-header">
                    <span className="bubble-name">Knowledge Assistant</span>
                  </div>
                  <div className="typing">
                    <span />
                    <span />
                    <span />
                  </div>
                  <p className="loading-text">Retrieving sources · Running ACL filter · Generating…</p>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="error-banner">
              <strong>Request failed</strong>
              <p>{error}</p>
            </div>
          )}

          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <div className="composer-inner">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about incidents, tickets, on-call, policies…"
                rows={2}
                disabled={loading || !persona}
              />
              <div className="composer-actions">
                <span className="hint">Enter to send · Shift+Enter for newline</span>
                <button type="submit" disabled={loading || !input.trim() || !persona}>
                  {loading ? "Working…" : "Send"}
                </button>
              </div>
            </div>
          </form>
        </main>

        <SourcesPanel citations={activeCitations || []} />
      </div>
    </div>
  );
}
