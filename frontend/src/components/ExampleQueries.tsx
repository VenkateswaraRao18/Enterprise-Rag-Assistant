type Props = {
  examples: string[];
  onSelect: (query: string) => void;
  layout?: "stack" | "scroll";
  disabled?: boolean;
  className?: string;
  label?: string;
};

export default function ExampleQueries({
  examples,
  onSelect,
  layout = "stack",
  disabled = false,
  className = "",
  label = "Demo queries",
}: Props) {
  if (!examples.length) return null;

  const scroll = layout === "scroll";

  return (
    <div
      className={`chat-examples ${scroll ? "chat-examples--scroll" : ""} ${className}`.trim()}
    >
      <span className={scroll ? "chat-examples-label" : "label"}>{label}</span>
      <div className={scroll ? "chat-examples-scroll" : "examples"}>
        {examples.map((q) => (
          <button
            key={q}
            type="button"
            className={`example-btn ${scroll ? "example-btn--chip" : ""}`}
            disabled={disabled}
            onClick={() => onSelect(q)}
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
