/**
 * Results summary panel showing comparison statistics.
 */
export default function ResultsPanel({ results }) {
  if (!results) return null;

  const {
    total_reference_notes: refTotal,
    total_played_notes: playedTotal,
    correct,
    wrong,
    late,
    early,
    missed,
  } = results;

  const accuracy = refTotal > 0
    ? Math.round((correct / refTotal) * 100)
    : 0;

  const stats = [
    { label: '✓ Correct', value: correct, color: '#4caf50' },
    { label: '✗ Wrong', value: wrong, color: '#f44336' },
    { label: '⏰ Late', value: late, color: '#ff9800' },
    { label: '⏩ Early', value: early, color: '#ffc107' },
    { label: '⊘ Missed', value: missed, color: '#9e9e9e' },
  ];

  return (
    <div className="results-panel">
      <h2>Results</h2>

      <div className="accuracy-badge">
        <span className="accuracy-value">{accuracy}%</span>
        <span className="accuracy-label">Accuracy</span>
      </div>

      <div className="stats-grid">
        {stats.map(({ label, value, color }) => (
          <div key={label} className="stat-card" style={{ borderLeftColor: color }}>
            <span className="stat-value">{value}</span>
            <span className="stat-label">{label}</span>
          </div>
        ))}
      </div>

      <div className="totals-row">
        <span>Reference notes: <strong>{refTotal}</strong></span>
        <span>Played notes: <strong>{playedTotal}</strong></span>
      </div>
    </div>
  );
}
