import { useEffect, useState } from "react";
import {
  COLORS,
  LABELS,
  MODELS,
  SCENARIOS,
  estimate,
  type Model,
  type Options,
  type Snapshot,
} from "./data";
export const fmt = (n: number, d = 3) =>
  n.toLocaleString("en-US", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
function useCompact() {
  const [small, set] = useState(
    () => window.matchMedia("(max-width: 640px)").matches,
  );
  useEffect(() => {
    const q = window.matchMedia("(max-width: 640px)");
    const update = () => set(q.matches);
    q.addEventListener("change", update);
    return () => q.removeEventListener("change", update);
  }, []);
  return small;
}
export function PolicyChart({
  data,
  reach,
  options,
  selected,
}: {
  data: Snapshot;
  reach: number;
  options: Options;
  selected: Model;
}) {
  const small = useCompact(),
    w = small ? 360 : 900,
    left = small ? 110 : 170,
    right = w - 30;
  const rows = MODELS.map((model) => ({
    model,
    ...estimate(data, model, reach, options),
  }));
  const lo = Math.min(0, ...rows.map((r) => r.low)),
    hi = Math.max(0, ...rows.map((r) => r.high));
  const pad = (hi - lo) * 0.09 || 1;
  const min = lo - pad,
    max = hi + pad;
  const x = (v: number) => left + ((v - min) / (max - min)) * (right - left);
  return (
    <div className="chart-wrap">
      <svg
        viewBox={`0 0 ${w} 322`}
        role="img"
        aria-label={`Saved ${options.interval} intervals at ${reach}% reach. All values are visits per 1,000 eligible records.`}
      >
        <title>Four fixed strategies at {reach}% reach</title>
        {Array.from({ length: 5 }, (_, i) => min + ((max - min) * i) / 4).map(
          (v, i) => (
            <g key={i}>
              <line x1={x(v)} x2={x(v)} y1="25" y2="267" className="gridline" />
              <text x={x(v)} y="290" textAnchor="middle" className="axis-label">
                {fmt(v, 1)}
              </text>
            </g>
          ),
        )}
        <line x1={x(0)} x2={x(0)} y1="24" y2="267" className="zero-line" />
        {rows.map((r, i) => {
          const y = 52 + i * 62;
          return (
            <g
              key={r.model}
              tabIndex={0}
              aria-label={`${LABELS[r.model]}: ${fmt(r.value)}, saved ${options.interval} interval ${fmt(r.low)} to ${fmt(r.high)}`}
            >
              <title>
                {LABELS[r.model]}: {fmt(r.value)} [{fmt(r.low)}, {fmt(r.high)}]
              </title>
              <text
                x={left - 16}
                y={y + 4}
                textAnchor="end"
                className={
                  r.model === selected ? "chart-name selected" : "chart-name"
                }
              >
                {LABELS[r.model]}
              </text>
              <line
                x1={x(r.low)}
                x2={x(r.high)}
                y1={y}
                y2={y}
                stroke={COLORS[r.model]}
                strokeWidth={r.model === selected ? 4 : 2.5}
              />
              <path
                d={`M${x(r.low)},${y - 7}v14 M${x(r.high)},${y - 7}v14`}
                stroke={COLORS[r.model]}
                strokeWidth="2"
              />
              <circle
                cx={x(r.value)}
                cy={y}
                r={r.model === selected ? 7 : 5}
                fill={COLORS[r.model]}
                stroke="var(--paper)"
                strokeWidth="2"
              />
            </g>
          );
        })}
        <text
          x={(left + right) / 2}
          y="318"
          textAnchor="middle"
          className="axis-label"
        >
          Additional visits / 1,000 eligible
        </text>
      </svg>
    </div>
  );
}
export function SensitivityChart({
  data,
  options,
}: {
  data: Snapshot;
  options: Options;
}) {
  const small = useCompact(),
    w = small ? 360 : 900,
    left = 48,
    right = w - 25;
  const rows = (["ipw", "dr"] as const).flatMap((method) =>
    SCENARIOS.map((e, i) => ({
      method,
      i,
      ...estimate(data, "all", 100, { ...options, method, propensity: e }),
    })),
  );
  const lo = Math.floor(Math.min(0, ...rows.map((r) => r.low)) / 5) * 5,
    hi = Math.ceil(Math.max(0, ...rows.map((r) => r.high)) / 5) * 5;
  const x = (i: number) => left + ((i + 0.5) * (right - left)) / 5,
    y = (v: number) => 240 - ((v - lo) / (hi - lo)) * 210;
  return (
    <div className="chart-wrap">
      <svg
        viewBox={`0 0 ${w} 305`}
        role="img"
        aria-label="Saved all-targeting IPW and shared DR estimates at exactly five assumed propensities. Points and saved intervals only; no interpolation."
      >
        <title>Propensity sensitivity: saved all-targeting reference</title>
        {Array.from({ length: 5 }, (_, i) => lo + ((hi - lo) * i) / 4).map(
          (v, i) => (
            <g key={i}>
              <line
                x1={left}
                x2={right}
                y1={y(v)}
                y2={y(v)}
                className="gridline"
              />
              <text
                x={left - 10}
                y={y(v) + 5}
                textAnchor="end"
                className="axis-label"
              >
                {fmt(v, 0)}
              </text>
            </g>
          ),
        )}
        <line x1={left} x2={right} y1={y(0)} y2={y(0)} className="zero-line" />
        {rows.map((r) => {
          const px = x(r.i) + (r.method === "dr" ? -6 : 6),
            color = r.method === "dr" ? "#26776b" : "#ae492d";
          return (
            <g
              key={`${r.method}-${r.i}`}
              tabIndex={0}
              aria-label={`${r.method === "dr" ? "Shared DR" : "IPW"}, assumed e=${SCENARIOS[r.i]}: ${fmt(r.value)}, interval ${fmt(r.low)} to ${fmt(r.high)}`}
            >
              <title>
                {r.method === "dr" ? "Shared DR" : "IPW"} · e={SCENARIOS[r.i]}:{" "}
                {fmt(r.value)} [{fmt(r.low)}, {fmt(r.high)}]
              </title>
              <line
                x1={px}
                x2={px}
                y1={y(r.low)}
                y2={y(r.high)}
                stroke={color}
                strokeWidth="2.5"
              />
              <circle cx={px} cy={y(r.value)} r="5" fill={color} />
            </g>
          );
        })}
        {SCENARIOS.map((e, i) => (
          <text
            key={e}
            x={x(i)}
            y="266"
            textAnchor="middle"
            className="axis-label"
          >
            {e.toFixed(e === 0.825 || e === 0.875 ? 3 : 2)}
          </text>
        ))}
        <text
          x={(left + right) / 2}
          y="298"
          textAnchor="middle"
          className="axis-label"
        >
          Assumed assignment probability
        </text>
      </svg>
      <div className="chart-key">
        <span>
          <i style={{ background: "#ae492d" }} /> IPW · reweighting
        </span>
        <span>
          <i style={{ background: "#26776b" }} /> Shared DR · outcome models +
          reweighting
        </span>
      </div>
    </div>
  );
}

export function fmtDecimal(
  value: { toFixed: (digits: number) => string },
  digits = 2,
) {
  const [whole, fraction] = value.toFixed(digits).split(".");
  return (
    whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",") +
    (fraction === undefined ? "" : "." + fraction)
  );
}
