// Pure-SVG chart primitives — no chart library, matches the reference app look.

const PALETTE = ["#1b3b6f", "#2f6df6", "#3fa7d6", "#5bc8af", "#f0a202", "#e8833a", "#9aa7bd"];
export const seriesColor = (i: number) => PALETTE[i % PALETTE.length];

// ---- Line chart: fraud rate over time (single series, area fill) ----
export function LineChart({
  points,
  height = 190,
  color = "#2f6df6",
  yFmt = (v: number) => v.toFixed(0),
}: {
  points: { label: string; value: number }[];
  height?: number;
  color?: string;
  yFmt?: (v: number) => string;
}) {
  if (!points || points.length < 2)
    return <div className="chart-empty">Not enough data</div>;
  const W = 720;
  const H = height;
  const pad = { l: 44, r: 14, t: 14, b: 26 };
  const ys = points.map((p) => p.value);
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys) * 1.1 || 1;
  const px = (i: number) => pad.l + (i / (points.length - 1)) * (W - pad.l - pad.r);
  const py = (v: number) => pad.t + (1 - (v - minY) / (maxY - minY || 1)) * (H - pad.t - pad.b);
  const line = points.map((p, i) => `${i === 0 ? "M" : "L"} ${px(i).toFixed(1)} ${py(p.value).toFixed(1)}`).join(" ");
  const area = `${line} L ${px(points.length - 1).toFixed(1)} ${py(minY).toFixed(1)} L ${px(0).toFixed(1)} ${py(minY).toFixed(1)} Z`;
  const ticks = 4;
  const gridY = Array.from({ length: ticks + 1 }, (_, i) => minY + ((maxY - minY) * i) / ticks);
  const nLabels = Math.min(points.length, 8);
  const step = Math.max(1, Math.floor(points.length / nLabels));
  return (
    <svg className="line-chart" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="area-grad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.18" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {gridY.map((g, i) => (
        <g key={i}>
          <line x1={pad.l} x2={W - pad.r} y1={py(g)} y2={py(g)} className="c-grid" />
          <text x={6} y={py(g) + 3} className="c-axis">{yFmt(g)}</text>
        </g>
      ))}
      {points.filter((_, i) => i % step === 0).map((p, i) => (
        <text key={i} x={px(points.indexOf(p))} y={H - 8} className="c-axis" textAnchor="middle">
          {p.label.slice(2)}
        </text>
      ))}
      <path d={area} fill="url(#area-grad)" stroke="none" />
      <path d={line} fill="none" stroke={color} strokeWidth={2} />
    </svg>
  );
}

// ---- Horizontal bar chart: fraud rate by region / policy ----
export function BarChart({
  rows,
  valueFmt = (v: number) => `${(v * 100).toFixed(1)}%`,
}: {
  rows: { label: string; value: number; sub?: string }[];
  valueFmt?: (v: number) => string;
}) {
  if (!rows.length) return <div className="chart-empty">No data</div>;
  const max = Math.max(...rows.map((r) => r.value)) || 1;
  return (
    <div className="barchart">
      {rows.map((r, i) => (
        <div className="bar-row" key={i}>
          <div className="bar-label" title={r.label}>{r.label}</div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(r.value / max) * 100}%`, background: seriesColor(i) }} />
          </div>
          <div className="bar-val">{valueFmt(r.value)}{r.sub ? <span className="bar-sub"> {r.sub}</span> : null}</div>
        </div>
      ))}
    </div>
  );
}

// ---- Grouped column chart: risk-score distribution (fraud vs legit) ----
export function RiskColumns({
  buckets,
}: {
  buckets: { score: number; fraud: number; legit: number }[];
}) {
  if (!buckets.length) return <div className="chart-empty">No data</div>;
  const W = 460;
  const H = 200;
  const pad = { l: 40, r: 12, t: 14, b: 30 };
  const max = Math.max(...buckets.map((b) => b.fraud + b.legit)) || 1;
  const bw = (W - pad.l - pad.r) / buckets.length;
  const py = (v: number) => pad.t + (1 - v / max) * (H - pad.t - pad.b);
  const ticks = 4;
  const gridY = Array.from({ length: ticks + 1 }, (_, i) => (max * i) / ticks);
  return (
    <svg className="risk-cols" viewBox={`0 0 ${W} ${H}`}>
      {gridY.map((g, i) => (
        <g key={i}>
          <line x1={pad.l} x2={W - pad.r} y1={py(g)} y2={py(g)} className="c-grid" />
          <text x={6} y={py(g) + 3} className="c-axis">{Math.round(g)}</text>
        </g>
      ))}
      {buckets.map((b, i) => {
        const x = pad.l + i * bw + bw * 0.22;
        const w = bw * 0.56;
        const total = b.fraud + b.legit;
        const yTotal = py(total);
        const yFraud = py(b.fraud);
        return (
          <g key={i}>
            {/* legit (bottom) */}
            <rect x={x} y={yFraud} width={w} height={H - pad.b - yFraud} fill="#c7d2e4" rx={2} />
            {/* fraud (top, red) */}
            <rect x={x} y={yTotal} width={w} height={yFraud - yTotal} fill="#e2483b" rx={2} />
            <text x={x + w / 2} y={H - 12} className="c-axis" textAnchor="middle">{b.score}</text>
          </g>
        );
      })}
    </svg>
  );
}

// ---- Donut (used for fraud vs legit split) ----
export function Donut({
  segments,
  size = 140,
}: {
  segments: { label: string; value: number; color: string }[];
  size?: number;
}) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const r = size / 2 - 12;
  const cx = size / 2;
  const cy = size / 2;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <g transform={`rotate(-90 ${cx} ${cy})`}>
        {segments.map((s, i) => {
          const frac = s.value / total;
          const dash = frac * circ;
          const el = (
            <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color}
              strokeWidth={16} strokeDasharray={`${dash} ${circ - dash}`} strokeDashoffset={-offset} />
          );
          offset += dash;
          return el;
        })}
      </g>
    </svg>
  );
}
