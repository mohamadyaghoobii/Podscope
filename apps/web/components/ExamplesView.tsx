import { ExampleManifest } from "../lib/api";

const intentLabel: Record<ExampleManifest["intent"], string> = {
  risky: "Risky",
  hardened: "Hardened",
  reference: "Reference"
};

export function ExamplesView({
  examples,
  onLoad
}: {
  examples: ExampleManifest[];
  onLoad: (example: ExampleManifest) => void;
}) {
  return (
    <div className="examples-view">
      <div className="view-head">
        <h2>Sample manifests</h2>
        <p>Load any sample into the editor and run a review. Each one is safe demo YAML with no real secrets.</p>
      </div>
      <div className="examples-grid">
        {examples.map((example) => (
          <article className={`example-card intent-${example.intent}`} key={example.name}>
            <div className="example-card-head">
              <span className={`example-intent intent-${example.intent}`}>{intentLabel[example.intent]}</span>
              <span className="example-file">{example.name}</span>
            </div>
            <h3>{example.title}</h3>
            <p>{example.description}</p>
            <button className="primary-button" onClick={() => onLoad(example)}>
              Load &amp; analyze
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}
