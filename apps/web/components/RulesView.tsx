"use client";

import { useMemo, useState } from "react";
import { RuleInfo } from "../lib/api";
import { CATEGORIES, SEVERITY_LABEL } from "../lib/format";

export function RulesView({ rules }: { rules: RuleInfo[] }) {
  const [category, setCategory] = useState<string>("all");

  const filtered = useMemo(
    () => (category === "all" ? rules : rules.filter((rule) => rule.category === category)),
    [rules, category]
  );

  const tabs = ["all", ...CATEGORIES];

  return (
    <div className="rules-view">
      <div className="view-head">
        <div>
          <h2>Rule catalog</h2>
          <p>{rules.length} deterministic checks across six categories. Every finding maps back to one of these rules.</p>
        </div>
      </div>
      <div className="filter-tabs">
        {tabs.map((tab) => (
          <button key={tab} className={`filter-tab ${category === tab ? "is-active" : ""}`} onClick={() => setCategory(tab)}>
            {tab === "all" ? "All" : tab}
          </button>
        ))}
      </div>
      <div className="rules-grid">
        {filtered.map((rule) => (
          <article className="rule-card" key={rule.id}>
            <div className="rule-card-head">
              <span className="rule-id">{rule.id}</span>
              <span className={`badge badge-${rule.severity}`}>{SEVERITY_LABEL[rule.severity]}</span>
            </div>
            <h3>{rule.title}</h3>
            <p>{rule.description}</p>
            <div className="rule-card-foot">
              <span className="rule-category">{rule.category}</span>
              <span className="rule-confidence">{rule.confidence} confidence</span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
