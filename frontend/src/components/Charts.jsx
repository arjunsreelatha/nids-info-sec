import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { THREATS } from "../mockData.js";

const COLORS = ["#1b5e20", "#2e7d32", "#43a047", "#66bb6a", "#81c784", "#a5d6a7"];

export default function Charts({ events }) {
  const byThreat = THREATS.map((t) => ({ name: t, count: events.filter((e) => e.threat_type === t).length }));
  const size = Math.max(1, Math.ceil(events.length / 10));
  const timeline = Array.from({ length: 10 }, (_, i) => {
    const slice = events.slice(i * size, (i + 1) * size);
    return {
      time: slice[0] ? new Date(slice[0].timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "",
      attacks: slice.filter((e) => e.prediction === "attack").length,
      normal: slice.filter((e) => e.prediction === "normal").length,
    };
  });
  return (
    <section className="grid">
      <div className="panel">
        <h3>Threat categories</h3>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={byThreat}>
            <CartesianGrid strokeDasharray="3 3" stroke="#c8e6c9" />
            <XAxis dataKey="name" stroke="#4f6f57" fontSize={11} />
            <YAxis allowDecimals={false} stroke="#4f6f57" />
            <Tooltip />
            <Bar dataKey="count">{byThreat.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="panel">
        <h3>Distribution</h3>
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie data={byThreat.filter((d) => d.count)} dataKey="count" nameKey="name" outerRadius={85} label>
              {byThreat.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="panel wide">
        <h3>Security event timeline</h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#c8e6c9" />
            <XAxis dataKey="time" stroke="#4f6f57" fontSize={11} />
            <YAxis allowDecimals={false} stroke="#4f6f57" />
            <Tooltip />
            <Legend />
            <Line dataKey="attacks" stroke="#b71c1c" strokeWidth={2} />
            <Line dataKey="normal" stroke="#2e7d32" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
