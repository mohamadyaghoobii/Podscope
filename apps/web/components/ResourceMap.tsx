import { AnalysisResult, ResourceSummary } from "../lib/api";

function groupByNamespace(resources: ResourceSummary[]) {
  const groups = new Map<string, ResourceSummary[]>();
  for (const resource of resources) {
    const key = resource.namespace || "default";
    const bucket = groups.get(key) || [];
    bucket.push(resource);
    groups.set(key, bucket);
  }
  return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

export function ResourceMap({ result }: { result: AnalysisResult }) {
  const groups = groupByNamespace(result.resources);

  return (
    <div className="resource-map">
      {groups.map(([namespace, resources]) => (
        <div className="ns-group" key={namespace}>
          <div className="ns-header">
            <span className="ns-label">namespace</span>
            <span className="ns-name">{namespace}</span>
            <span className="ns-count">{resources.length}</span>
          </div>
          <div className="ns-nodes">
            {resources.map((resource) => (
              <div
                className={`resource-node ${resource.top_severity ? `sev-${resource.top_severity}` : "sev-clean"}`}
                key={`${resource.kind}-${resource.name}`}
                title={resource.images.join(", ")}
              >
                <span className="node-kind">{resource.kind}</span>
                <span className="node-name">{resource.name}</span>
                <span className="node-meta">
                  {resource.containers.length > 0 && <span>{resource.containers.length} ctr</span>}
                  <span className={resource.finding_count ? "node-issues" : "node-clean"}>
                    {resource.finding_count ? `${resource.finding_count} issue${resource.finding_count > 1 ? "s" : ""}` : "clean"}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
