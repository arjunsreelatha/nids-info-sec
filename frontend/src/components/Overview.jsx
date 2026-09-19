export default function Overview({ events }) {
  const attacks = events.filter((e) => e.prediction === "attack");
  const active = attacks.filter((e) => e.status !== "resolved");
  const cards = [
    ["System status", "Operational", "ok"],
    ["Total events", events.length, ""],
    ["Detected threats", attacks.length, "bad"],
    ["Safe events", events.length - attacks.length, "ok"],
    ["Active alerts", active.length, "warn"],
  ];
  return (
    <section className="cards">
      {cards.map(([label, value, tone]) => (
        <div className={`card ${tone}`} key={label}>
          <div className="label">{label}</div>
          <div className="value">{value}</div>
        </div>
      ))}
    </section>
  );
}
