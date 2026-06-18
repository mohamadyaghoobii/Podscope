import { Scorecard } from "../lib/api";
import { STATUS_LABEL, gradeTone } from "../lib/format";

export function ScoreCard({ card }: { card: Scorecard }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const progress = circumference * (1 - card.score / 100);
  const tone = gradeTone(card.grade);
  const passRatio = card.checks_run ? Math.round((card.checks_passed / card.checks_run) * 100) : 0;

  return (
    <div className={`score-card tone-${tone}`}>
      <div className="score-ring">
        <svg viewBox="0 0 128 128" width="128" height="128">
          <circle cx="64" cy="64" r={radius} className="ring-track" />
          <circle
            cx="64"
            cy="64"
            r={radius}
            className="ring-value"
            strokeDasharray={circumference}
            strokeDashoffset={progress}
            transform="rotate(-90 64 64)"
          />
        </svg>
        <div className="score-center">
          <span className="score-value">{card.score}</span>
          <span className="score-out">/ 100</span>
        </div>
      </div>
      <div className="score-meta">
        <div className="score-row">
          <span className={`grade-chip tone-${tone}`}>Grade {card.grade}</span>
          <span className={`status-chip status-${card.status}`}>{STATUS_LABEL[card.status]}</span>
        </div>
        <p className="score-explanation">{card.explanation}</p>
        <div className="checks-bar" role="img" aria-label={`${card.checks_passed} of ${card.checks_run} checks passed`}>
          <div className="checks-fill" style={{ width: `${passRatio}%` }} />
        </div>
        <div className="checks-legend">
          <span>{card.checks_passed} passed</span>
          <span>{card.checks_failed} failed</span>
          <span>{card.checks_run} checks</span>
        </div>
      </div>
    </div>
  );
}
