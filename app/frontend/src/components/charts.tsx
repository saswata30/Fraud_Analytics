// Interactive SVG charts with hover tooltips — dark theme, no chart library.
import { useState } from "react";

const PALETTE = ["#4f8bff", "#ff6b5e", "#2dd4bf", "#f5b83d", "#a78bfa", "#f0883e", "#8aa0bd"];
export const seriesColor = (i: number) => PALETTE[i % PALETTE.length];

interface Tip {
  x: number;
  y: number;
  title: string;
  rows: { label: string; value: string; color: string }[];
}

function Tooltip({ tip }: { tip: Tip | null }) {
  if (!tip) return null;
  return (
    <div className="chart-tip" style={{ left: tip.x, top: tip.y }}>
      <div className="chart-tip-title">{tip.title}</div>
      {tip.rows.map((r, i) => (
        <div className="chart-tip-row" key={i}>
          <i style={{ background: r.color }} />
          <span>{r.label}</span>
          <b>{r.value}</b>
        </div>
      ))}
    </div>
  );
}

// ---- Multi-series line/area chart with a hover crosshair + tooltip ----
export function LineArea({
  data,
  xKey,
  series,
  height = 240,
  yFmt = (v: number) => v.toLocaleString(),
  fill = true,
}: {
  data: Record<string, any>[];
  xKey: string;
  series: { key: string; label: string; color: string }[];
  height?: number;
  yFmt?: (v: number) => string;
  fill?: boolean;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const [tip, setTip] = useState<Tip | null>(null);
  if (!data || data.length < 2) return <div className="chart-empty">Not enough data</div>;

  const W = 760;
  const H = height;
  const pad = { l: 46, r: 16, t: 16, b: 34 };
  const iw = W - pad.l - pad.r;
  const ih = H - pad.t - pad.b;
  const vals = data.flatMap((d) => series.map((s) => Number(d[s.key]))).filter((v) => !isNaN(v));
  const maxY = Math.max(...vals, 0) * 1.12 || 1;
  const minY = Math.min(...vals, 0);
  const px = (i: number) => pad.l + (i / (data.length - 1)) * iw;
  const py = (v: number) => pad.t + (1 - (v - minY) / (maxY - minY || 1)) * ih;
  const ticks = 4;
  const gridY = Array.from({ length: ticks + 1 }, (_, i) => minY + ((maxY - minY) * i) / ticks);
  const step = Math.max(1, Math.ceil(data.length / 9));

  function onMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const rx = ((e.clientX - rect.left) / rect.width) * W;
    let idx = Math.round(((rx - pad.l) / iw) * (data.length - 1));
    idx = Math.max(0, Math.min(data.length - 1, idx));
    setHover(idx);
    setTip({
      x: (px(idx) / W) * rect.width,
      y: pad.t,
      title: String(data[idx][xKey] ?? ""),
      rows: series.map((s) => ({
        label: s.label,
        value: yFmt(Number(data[idx][s.key]) || 0),
        color: s.color,
      })),
    });
  }

  return (
    <div className="chart-wrap" onMouseLeave={() => { setHover(null); setTip(null); }}>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" className="chart-svg" onMouseMove={onMove}>
        <defs>
          {series.map((s, si) => (
            <linearGradient id={`grad-${si}`} key={si} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={s.color} stopOpacity="0.22" />
              <stop offset="100%" stopColor={s.color} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>
        {gridY.map((g, i) => (
          <g key={i}>
            <line x1={pad.l} x2={W - pad.r} y1={py(g)} y2={py(g)} className="c-grid" />
            <text x={pad.l - 8} y={py(g) + 3} className="c-axis" textAnchor="end">{yFmt(g)}</text>
          </g>
        ))}
        {series.map((s, si) => {
          const line = data.map((d, i) => `${i === 0 ? "M" : "L"} ${px(i).toFixed(1)} ${py(Number(d[s.key]) || 0).toFixed(1)}`).join(" ");
          const area = `${line} L ${px(data.length - 1).toFixed(1)} ${py(minY).toFixed(1)} L ${px(0).toFixed(1)} ${py(minY).toFixed(1)} Z`;
          return (
            <g key={s.key}>
              {fill && <path d={area} fill={`url(#grad-${si})`} stroke="none" />}
              <path d={line} fill="none" stroke={s.color} strokeWidth={2.2} />
            </g>
          );
        })}
        {hover !== null && (
          <g>
            <line x1={px(hover)} x2={px(hover)} y1={pad.t} y2={H - pad.b} className="c-crosshair" />
            {series.map((s) => (
              <circle key={s.key} cx={px(hover)} cy={py(Number(data[hover][s.key]) || 0)} r={3.6} fill={s.color} stroke="#0e1626" strokeWidth={1.5} />
            ))}
          </g>
        )}
        {data.map((d, i) =>
          i % step === 0 ? (
            <text key={i} x={px(i)} y={H - 14} className="c-axis" textAnchor="middle">{String(d[xKey] ?? "")}</text>
          ) : null
        )}
      </svg>
      <Tooltip tip={tip} />
      <div className="chart-legend">
        {series.map((s) => (
          <span key={s.key}><i style={{ background: s.color }} /> {s.label}</span>
        ))}
      </div>
    </div>
  );
}

// ---- Horizontal bar chart with hover highlight + tooltip ----
export function BarChart({
  rows,
  valueFmt = (v: number) => `${(v * 100).toFixed(1)}%`,
  colorFn,
}: {
  rows: { label: string; value: number; sub?: string }[];
  valueFmt?: (v: number) => string;
  colorFn?: (i: number, v: number, max: number) => string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  if (!rows.length) return <div className="chart-empty">No data</div>;
  const max = Math.max(...rows.map((r) => r.value)) || 1;
  return (
    <div className="barchart">
      {rows.map((r, i) => {
        const color = colorFn ? colorFn(i, r.value, max) : seriesColor(i);
        return (
          <div className={`bar-row ${hover === i ? "hl" : ""}`} key={i}
            onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
            title={`${r.label}: ${valueFmt(r.value)}${r.sub ? " · " + r.sub : ""}`}>
            <div className="bar-label">{r.label}</div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(r.value / max) * 100}%`, background: color }} />
            </div>
            <div className="bar-val">{valueFmt(r.value)}{r.sub ? <span className="bar-sub"> {r.sub}</span> : null}</div>
          </div>
        );
      })}
    </div>
  );
}

// ---- Stacked risk columns (fraud vs legit) with hover tooltip ----
export function RiskColumns({
  buckets,
}: {
  buckets: { score: number; fraud: number; legit: number }[];
}) {
  const [hover, setHover] = useState<number | null>(null);
  const [tip, setTip] = useState<Tip | null>(null);
  if (!buckets.length) return <div className="chart-empty">No data</div>;
  const W = 480;
  const H = 220;
  const pad = { l: 40, r: 12, t: 16, b: 32 };
  const ih = H - pad.t - pad.b;
  const max = Math.max(...buckets.map((b) => b.fraud + b.legit)) || 1;
  const bw = (W - pad.l - pad.r) / buckets.length;
  const py = (v: number) => pad.t + (1 - v / max) * ih;
  const ticks = 4;
  const gridY = Array.from({ length: ticks + 1 }, (_, i) => (max * i) / ticks);
  return (
    <div className="chart-wrap" onMouseLeave={() => { setHover(null); setTip(null); }}>
      <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg">
        {gridY.map((g, i) => (
          <g key={i}>
            <line x1={pad.l} x2={W - pad.r} y1={py(g)} y2={py(g)} className="c-grid" />
            <text x={pad.l - 6} y={py(g) + 3} className="c-axis" textAnchor="end">{Math.round(g)}</text>
          </g>
        ))}
        {buckets.map((b, i) => {
          const x = pad.l + i * bw + bw * 0.2;
          const w = bw * 0.6;
          const total = b.fraud + b.legit;
          const yTotal = py(total);
          const yFraud = py(b.fraud);
          const active = hover === i;
          return (
            <g key={i} opacity={hover === null || active ? 1 : 0.5}
              onMouseEnter={(e) => {
                const rect = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect();
                setHover(i);
                setTip({
                  x: ((x + w / 2) / W) * rect.width, y: pad.t,
                  title: `Risk score ${b.score}`,
                  rows: [
                    { label: "Fraud", value: b.fraud.toLocaleString(), color: "#ff6b5e" },
                    { label: "Legitimate", value: b.legit.toLocaleString(), color: "#3b5578" },
                  ],
                });
              }}>
              <rect x={x} y={yFraud} width={w} height={H - pad.b - yFraud} fill="#3b5578" rx={3} />
              <rect x={x} y={yTotal} width={w} height={yFraud - yTotal} fill="#ff6b5e" rx={3} />
              <text x={x + w / 2} y={H - 12} className="c-axis" textAnchor="middle">{b.score}</text>
            </g>
          );
        })}
      </svg>
      <Tooltip tip={tip} />
    </div>
  );
}

// ---- Donut with hover-per-segment ----
export function Donut({
  segments,
  size = 150,
  centerTop,
  centerSub,
}: {
  segments: { label: string; value: number; color: string }[];
  size?: number;
  centerTop?: string;
  centerSub?: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="donut-holder" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <g transform={`rotate(-90 ${cx} ${cy})`}>
          {segments.map((s, i) => {
            const frac = s.value / total;
            const dash = frac * circ;
            const el = (
              <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color}
                strokeWidth={hover === i ? 18 : 14} strokeDasharray={`${dash} ${circ - dash}`}
                strokeDashoffset={-offset} opacity={hover === null || hover === i ? 1 : 0.5}
                onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}
                style={{ transition: "stroke-width .1s, opacity .1s", cursor: "pointer" }} />
            );
            offset += dash;
            return el;
          })}
        </g>
      </svg>
      {(centerTop || hover !== null) && (
        <div className="donut-center">
          <b>{hover !== null ? `${((segments[hover].value / total) * 100).toFixed(1)}%` : centerTop}</b>
          <span>{hover !== null ? segments[hover].label : centerSub}</span>
        </div>
      )}
    </div>
  );
}
