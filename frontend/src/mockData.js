export const THREATS = ["DDoS", "DoS", "Bot", "Brute force", "Infiltration", "Web"];
const SEVERITY = { DDoS: "critical", DoS: "high", Bot: "high", "Brute force": "medium", Infiltration: "critical", Web: "medium" };
const STATUSES = ["open", "investigating", "resolved"];

function rng(seed) {
  let s = seed;
  return () => ((s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296);
}

const INTERPRETATION = {
  DDoS: "Many sources flooding one target; volume pattern learned by the RF.",
  DoS: "Single-source resource exhaustion pattern.",
  Bot: "Periodic beacon-like flows typical of botnet command and control.",
  "Brute force": "Repeated short authentication-like connections to one service.",
  Infiltration: "Unusual internal flow; hard case, RF often misses this class.",
  Web: "Web attack pattern; rare class, weakest RF detection.",
};

export function makeMockEvents(n = 60) {
  const r = rng(42);
  const now = Date.now();
  return Array.from({ length: n }, (_, i) => {
    const isAttack = r() < 0.35;
    const threat = isAttack ? THREATS[Math.floor(r() * THREATS.length)] : "None";
    const rf = isAttack ? 0.5 + r() * 0.5 : r() * 0.15;
    const decidedByAE = isAttack && r() < 0.3;
    return {
      id: `evt-${String(i + 1).padStart(4, "0")}`,
      timestamp: new Date(now - (n - i) * 90000).toISOString(),
      event: isAttack ? `Suspicious flow to 10.0.${Math.floor(r() * 9)}.${Math.floor(r() * 250)}` : "Routine flow",
      prediction: isAttack ? "attack" : "normal",
      threat_type: threat,
      severity: isAttack ? SEVERITY[threat] : "low",
      confidence: Number((isAttack ? 0.7 + r() * 0.29 : 0.85 + r() * 0.14).toFixed(3)),
      status: isAttack ? STATUSES[Math.floor(r() * 3)] : "resolved",
      detail: {
        rf_probability: Number(rf.toFixed(3)),
        ae_error: Number((isAttack ? 0.02 + r() * 0.05 : r() * 0.01).toFixed(4)),
        decided_by: decidedByAE ? "AE" : "RF",
        interpretation: isAttack ? INTERPRETATION[threat] : "Below RF threshold T1; treated as normal traffic.",
      },
    };
  });
}
