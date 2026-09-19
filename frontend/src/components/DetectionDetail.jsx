export default function DetectionDetail({ event }) {
  if (!event) {
    return (
      <div className="panel">
        <h3>Detection detail</h3>
        <p className="muted">Click an event to inspect it.</p>
      </div>
    );
  }
  const d = event.detail;
  const steps = [
    ["Input event", `${event.id}: ${event.event}`],
    ["RF probability", `${d.rf_probability} (attack if > T1)`],
    ["AE reconstruction error", `${d.ae_error} (normal if <= T2)`],
    ["Prediction", `${event.prediction.toUpperCase()} (decided by ${d.decided_by})`],
    ["Threat category", event.threat_type],
    ["Confidence", `${(event.confidence * 100).toFixed(1)}%`],
    ["Security interpretation", d.interpretation],
  ];
  return (
    <div className="panel">
      <h3>Detection detail</h3>
      <ol className="steps">
        {steps.map(([k, v]) => <li key={k}><b>{k}</b><span>{v}</span></li>)}
      </ol>
    </div>
  );
}
