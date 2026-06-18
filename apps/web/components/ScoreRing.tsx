export function ScoreRing({ score }: { score: number }) {
  const label = score >= 90 ? "healthy" : score >= 65 ? "review" : "high risk";
  return (
    <div className="score-ring">
      <div className="score-value">{score}</div>
      <div className="score-label">{label}</div>
    </div>
  );
}
