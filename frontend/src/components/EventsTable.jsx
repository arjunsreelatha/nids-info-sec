const HEADERS = ["Timestamp", "Event", "Threat Type", "Severity", "Prediction", "Confidence", "Status"];

export default function EventsTable({ events, selectedId, onSelect }) {
  const rows = [...events].reverse().slice(0, 15);
  return (
    <div className="panel">
      <h3>Recent security events</h3>
      <div className="scroll">
        <table>
          <thead>
            <tr>{HEADERS.map((h) => <th key={h}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.id} className={e.id === selectedId ? "selected" : ""} onClick={() => onSelect(e.id)}>
                <td>{new Date(e.timestamp).toLocaleTimeString()}</td>
                <td>{e.event}</td>
                <td>{e.threat_type}</td>
                <td><span className={`badge ${e.severity}`}>{e.severity}</span></td>
                <td>{e.prediction}</td>
                <td>{(e.confidence * 100).toFixed(1)}%</td>
                <td>{e.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
