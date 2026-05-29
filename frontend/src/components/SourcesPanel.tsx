import type { Citation } from "../types";
import { groupCitationsByType, parseTitle, sourceIcon, sourceLabel } from "../utils/format";

type Props = {
  citations: Citation[];
};

export default function SourcesPanel({ citations }: Props) {
  const groups = groupCitationsByType(citations);

  return (
    <aside className="panel sources-panel">
      <div className="panel-head">
        <h2>Evidence</h2>
        <p>Grounded context used for the latest answer</p>
      </div>

      {!citations.length ? (
        <div className="panel-empty">
          <div className="empty-icon">📎</div>
          <p>No sources selected</p>
          <span>Run a query to inspect citations and source links.</span>
        </div>
      ) : (
        <div className="sources-list">
          {Object.entries(groups).map(([type, items]) => (
            <section key={type} className="source-group">
              <h3>
                <span>{sourceIcon(type)}</span> {sourceLabel(type)}
                <span className="count">{items.length}</span>
              </h3>
              {items.map((c) => {
                const meta = parseTitle(c.title);
                return (
                  <article key={c.ref} className="source-card">
                    <div className="source-card-top">
                      <span className="ref-badge">[{c.ref}]</span>
                      <span className={`type-badge type-${type}`}>{type}</span>
                    </div>
                    <h4>{meta.channel || c.title}</h4>
                    {meta.time && <p className="meta-line">{meta.time}</p>}
                    {meta.author && <p className="meta-line">{meta.author}</p>}
                    <p className="source-id">{c.source_id}</p>
                    {c.source_url && (
                      <a href={c.source_url} target="_blank" rel="noreferrer" className="source-link">
                        Open in source system ↗
                      </a>
                    )}
                  </article>
                );
              })}
            </section>
          ))}
        </div>
      )}
    </aside>
  );
}
