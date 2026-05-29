import type { Persona } from "../types";

type Props = {
  personas: Persona[];
  personaIdx: number;
  onPersonaChange: (idx: number) => void;
  examples: string[];
  onExample: (q: string) => void;
  onClearChat: () => void;
};

export default function Sidebar({
  personas,
  personaIdx,
  onPersonaChange,
  examples,
  onExample,
  onClearChat,
}: Props) {
  const persona = personas[personaIdx];

  return (
    <aside className="panel sidebar">
      <div className="sidebar-section">
        <label className="label">Active identity</label>
        <div className="persona-list">
          {personas.map((p, i) => (
            <button
              key={`${p.team}-${p.role}-${i}`}
              type="button"
              className={`persona-card ${i === personaIdx ? "active" : ""}`}
              onClick={() => onPersonaChange(i)}
            >
              <span className="persona-card-title">{p.label}</span>
              <span className="persona-card-meta">
                {p.team} · {p.role}
              </span>
            </button>
          ))}
        </div>
      </div>

      {persona && (
        <div className="acl-card">
          <span className="label">Access context</span>
          <div className="acl-grid">
            <div>
              <span className="acl-key">Team</span>
              <span className="acl-val">{persona.team}</span>
            </div>
            <div>
              <span className="acl-key">Role</span>
              <span className="acl-val">{persona.role}</span>
            </div>
            <div>
              <span className="acl-key">Clearance</span>
              <span className="acl-val">{persona.clearance}</span>
            </div>
          </div>
        </div>
      )}

      <div className="sidebar-section grow">
        <div className="section-head">
          <label className="label">Suggested prompts</label>
        </div>
        <div className="examples">
          {examples.map((q) => (
            <button key={q} type="button" className="example-btn" onClick={() => onExample(q)}>
              {q}
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-actions">
        <button type="button" className="btn-ghost" onClick={onClearChat}>
          Clear conversation
        </button>
      </div>

      <div className="sidebar-arch">
        <span className="label">Pipeline</span>
        <div className="arch-tags">
          <span>ACL</span>
          <span>BM25</span>
          <span>Qdrant</span>
          <span>RRF</span>
          <span>Ollama</span>
        </div>
      </div>
    </aside>
  );
}
