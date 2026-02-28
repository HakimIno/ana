"use client";

import { useMemo, useRef, useEffect, useState } from "react";
import {
    AreaChart, Area,
    BarChart, Bar, Cell,
    LineChart, Line,
    PieChart, Pie,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend,
} from "recharts";


const T = {
    bg: "var(--ec-bg,      #fff)",
    surface: "var(--ec-surface, #f4f4f5)",
    border: "var(--ec-border,  rgba(0,0,0,0.08))",
    grid: "var(--ec-grid,    rgba(0,0,0,0.04))",
    dot: "var(--ec-dot,     rgba(0,0,0,0.08))",
    text: "var(--ec-text,    #09090b)",
    muted: "var(--ec-muted,   #71717a)",
    // Accent colors — blue + green, exactly like evilcharts
    a1: "var(--ec-accent1, oklch(51.1% 0.262 276.966))",
    a2: "var(--ec-accent2, #22c55e)",
} as const;

const SERIES = [T.a1, T.a2, "#f59e0b", "#ec4899", "#90f755ff"];

// ─── Types ────────────────────────────────────────────────────────────────────
type ChartKind = "bar" | "area" | "line" | "pie" | "radar";
interface RawItem { [k: string]: any }
interface Datum { label: string; value: number;[k: string]: any }

// ─── Utilities ────────────────────────────────────────────────────────────────
function pickType(hint: string, data: Datum[]): ChartKind {
    const t = (hint || "").toLowerCase();
    if (["pie", "donut", "proportion"].includes(t)) return "pie";
    if (["radar", "spider"].includes(t)) return "radar";
    if (t === "line") return "line";
    if (["area", "trend"].includes(t)) return "area";
    if (t === "bar" || t === "column") return "bar";
    const isTime = data.some(d =>
        /\d{4}[-\/]\d{1,2}/.test(d.label) ||
        /jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec/i.test(d.label) ||
        /q[1-4]/i.test(d.label) ||
        /ม\.ค|ก\.พ|มี\.ค|เม\.ย|พ\.ค|มิ\.ย|ก\.ค|ส\.ค|ก\.ย|ต\.ค|พ\.ย|ธ\.ค/.test(d.label)
    );
    if (isTime) return "area";
    if (data.length <= 6) return "pie";
    return "bar";
}

function normalise(raw: RawItem[]): Datum[] {
    if (!raw?.length) return [];
    return raw.map(item => {
        const label =
            item.label ?? item.name ?? item.branch ?? item.category ??
            item.month ?? item.year ?? item.date ?? item.period ??
            item.dept ?? item.department ?? item.product ?? item.type ??
            item.region ?? item.item ??
            (() => { const k = Object.keys(item).find(k => typeof item[k] === "string"); return k ? item[k] : "—" })();
        const value =
            item.value ?? item.count ?? item.total ?? item.revenue ??
            item.score ?? item.amount ?? item.avg ?? item.average ??
            item.salary ?? item.sales ?? item.profit ?? item.cost ??
            (() => { const k = Object.keys(item).find(k => typeof item[k] === "number"); return k ? item[k] : 0 })();
        return { ...item, label: String(label), value: Number(value) };
    });
}

const fmt = (v: number) =>
    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M`
        : v >= 1_000 ? `${(v / 1_000).toFixed(1)}k`
            : v % 1 !== 0 ? v.toFixed(1)
                : v.toLocaleString();

const truncLabel = (s: string, max = 18) =>
    s.length > max ? s.slice(0, max) + "…" : s;

// ─── Dot-grid SVG pattern ─────────────────────────────────────────────────────
const DotPattern = ({ id }: { id: string }) => (
    <defs>
        <pattern id={id} x={0} y={0} width={12} height={12} patternUnits="userSpaceOnUse">
            <circle cx={6} cy={6} r={0.85} fill={T.dot} />
        </pattern>
    </defs>
);

// ─── Tooltip ──────────────────────────────────────────────────────────────────
const Tip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
        <div style={{
            background: T.surface,
            border: `1px solid ${T.border}`,
            borderRadius: 10,
            padding: "8px 14px",
            boxShadow: "0 8px 30px rgba(0,0,0,0.5)",
            fontSize: 12,
            fontFamily: "inherit",
        }}>
            <div style={{ color: T.muted, fontWeight: 600, marginBottom: 4, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                {label || payload[0]?.payload?.label}
            </div>
            {payload.map((p: any, i: number) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ width: 7, height: 7, borderRadius: "50%", background: p.fill || p.stroke || T.a1, display: "inline-block", flexShrink: 0 }} />
                    <span style={{ color: T.text, fontWeight: 700, fontSize: 14 }}>{fmt(p.value)}</span>
                </div>
            ))}
        </div>
    );
};

// ─── Axis shared style ────────────────────────────────────────────────────────
const AX = { fill: T.muted, fontSize: 11, fontWeight: 500 as const };

// ─── % change badge (evilcharts header element) ───────────────────────────────
function ChangeBadge({ data }: { data: Datum[] }) {
    if (data.length < 2) return null;
    const first = data[0].value;
    const last = data[data.length - 1].value;
    if (first === 0) return null;
    const pct = ((last - first) / first) * 100;
    const up = pct >= 0;
    const clr = up ? "#22c55e" : "#ef4444";
    const bg = up ? "#14532d" : "#7f1d1d";
    return (
        <span style={{
            display: "inline-flex", alignItems: "center", gap: 3,
            fontSize: 12, fontWeight: 700, color: clr,
            background: bg, borderRadius: 5, padding: "2px 8px",
        }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"
                style={{ transform: up ? "none" : "scaleY(-1)" }}>
                <path d="M6 9.5V2.5M6 2.5L2.5 6M6 2.5L9.5 6"
                    stroke={clr} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            {up ? "+" : ""}{Math.abs(pct).toFixed(1)}%
        </span>
    );
}

// ─── Sub-chart components ─────────────────────────────────────────────────────
interface Sub { data: Datum[]; pid: string; animate: boolean }

function BarC({ data, pid, animate }: Sub) {
    const [hov, setHov] = useState<number | null>(null);
    return (
        <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 24 }} barCategoryGap="30%"
                onMouseLeave={() => setHov(null)}>
                <DotPattern id={pid} />
                <rect width="100%" height="100%" fill={`url(#${pid})`} />
                <CartesianGrid vertical={false} stroke={T.grid} />
                <XAxis dataKey="label" axisLine={false} tickLine={false}
                    tick={{ ...AX, textAnchor: "end" }} angle={-38} dy={6} dx={-4}
                    tickFormatter={(v: string) => truncLabel(v)} interval={0} height={60} />
                <YAxis axisLine={false} tickLine={false} tick={AX} tickFormatter={fmt} width={48} />
                <Tooltip content={<Tip />} cursor={{ fill: "rgba(0,0,0,0.05)" }} isAnimationActive={false} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}
                    isAnimationActive={animate} animationDuration={600}
                    onMouseEnter={(_: any, i: number) => setHov(i)}
                    onMouseLeave={() => setHov(null)}>
                    {data.map((_, i) => (
                        <Cell key={i} fill={T.a1}
                            opacity={hov === null || hov === i ? 1 : 0.35}
                            style={{ transition: "opacity 120ms" }} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
}

function AreaC({ data, pid, animate }: Sub) {
    const gid = `${pid}-g`;
    return (
        <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 24 }}>
                <defs>
                    <DotPattern id={pid} />
                    <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={T.a1} stopOpacity={0.25} />
                        <stop offset="100%" stopColor={T.a1} stopOpacity={0} />
                    </linearGradient>
                </defs>
                <rect width="100%" height="100%" fill={`url(#${pid})`} />
                <CartesianGrid vertical={false} stroke={T.grid} />
                <XAxis dataKey="label" axisLine={false} tickLine={false}
                    tick={{ ...AX, textAnchor: "end" }} angle={-38} dy={6} dx={-4}
                    tickFormatter={(v: string) => truncLabel(v)} interval={0} height={60} />
                <YAxis axisLine={false} tickLine={false} tick={AX} tickFormatter={fmt} width={48} />
                <Tooltip content={<Tip />} isAnimationActive={false} />
                <Area type="monotone" dataKey="value"
                    stroke={T.a1} strokeWidth={2} fill={`url(#${gid})`} dot={false}
                    activeDot={{ r: 4, fill: T.a1, stroke: T.bg, strokeWidth: 2 }}
                    isAnimationActive={animate} animationDuration={800} />
            </AreaChart>
        </ResponsiveContainer>
    );
}

function LineC({ data, pid, animate }: Sub) {
    return (
        <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 24 }}>
                <DotPattern id={pid} />
                <rect width="100%" height="100%" fill={`url(#${pid})`} />
                <CartesianGrid vertical={false} stroke={T.grid} />
                <XAxis dataKey="label" axisLine={false} tickLine={false}
                    tick={{ ...AX, textAnchor: "end" }} angle={-38} dy={6} dx={-4}
                    tickFormatter={(v: string) => truncLabel(v)} interval={0} height={60} />
                <YAxis axisLine={false} tickLine={false} tick={AX} tickFormatter={fmt} width={48} />
                <Tooltip content={<Tip />} isAnimationActive={false} />
                <Line type="monotone" dataKey="value"
                    stroke={T.a1} strokeWidth={2}
                    dot={{ r: 3, fill: T.bg, stroke: T.a1, strokeWidth: 1.5 }}
                    activeDot={{ r: 5, fill: T.a1, stroke: T.bg, strokeWidth: 2 }}
                    isAnimationActive={animate} animationDuration={800} />
            </LineChart>
        </ResponsiveContainer>
    );
}

function PieC({ data, animate }: Omit<Sub, "pid">) {
    const [hov, setHov] = useState<number | null>(null);
    const R = Math.PI / 180;
    const renderLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, value }: any) => {
        const r = innerRadius + (outerRadius - innerRadius) * 0.55;
        return (
            <text x={cx + r * Math.cos(-midAngle * R)} y={cy + r * Math.sin(-midAngle * R)}
                fill="#fff" textAnchor="middle" dominantBaseline="central"
                style={{ fontSize: 11, fontWeight: 700 }}>
                {fmt(value)}
            </text>
        );
    };
    return (
        <ResponsiveContainer width="100%" height={240}>
            <PieChart onMouseLeave={() => setHov(null)}>
                <Pie data={data} cx="50%" cy="46%"
                    innerRadius={0} outerRadius={90}
                    dataKey="value" nameKey="label"
                    paddingAngle={2} cornerRadius={3}
                    isAnimationActive={animate} animationDuration={700}
                    stroke={T.bg} strokeWidth={2}
                    label={renderLabel} labelLine={false}
                    onMouseEnter={(_: any, i: number) => setHov(i)}
                    onMouseLeave={() => setHov(null)}>
                    {data.map((_, i) => (
                        <Cell key={i} fill={SERIES[i % SERIES.length]}
                            opacity={hov === null || hov === i ? 1 : 0.35}
                            style={{ transition: "opacity 120ms" }} />
                    ))}
                </Pie>
                <Tooltip content={<Tip />} isAnimationActive={false} />
                <Legend iconType="circle" iconSize={7}
                    wrapperStyle={{ paddingTop: 8 }}
                    formatter={(v: any) => (
                        <span style={{ color: T.muted, fontSize: 11, fontWeight: 500 }}>{v}</span>
                    )} />
            </PieChart>
        </ResponsiveContainer>
    );
}

function RadarC({ data, animate }: Omit<Sub, "pid">) {
    return (
        <ResponsiveContainer width="100%" height={230}>
            <RadarChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 24 }}>
                <PolarGrid stroke={T.grid} />
                <PolarAngleAxis dataKey="label" tick={{ fill: T.muted, fontSize: 10, fontWeight: 500 }} />
                <PolarRadiusAxis tick={false} axisLine={false} />
                <Radar dataKey="value"
                    fill={T.a1} fillOpacity={0.12} stroke={T.a1} strokeWidth={1.5}
                    isAnimationActive={animate} animationDuration={800} />
                <Tooltip content={<Tip />} isAnimationActive={false} />
            </RadarChart>
        </ResponsiveContainer>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────
interface Props {
    data: RawItem[]
    title?: string
    subtitle?: string
    type?: string
}

export default function MetricsChart({ data: raw, title, subtitle, type = "bar" }: Props) {
    const data = useMemo(() => normalise(raw), [raw]);
    const kind = useMemo(() => pickType(type, data), [type, data]);

    const mounted = useRef(false);
    const [animate, setAnimate] = useState(true);
    useEffect(() => {
        if (!mounted.current) {
            mounted.current = true;
            const t = setTimeout(() => setAnimate(false), 1400);
            return () => clearTimeout(t);
        }
    }, []);

    const pid = useMemo(() => `ec${Math.random().toString(36).slice(2, 7)}`, []);

    if (!data.length) return null;

    const chart = (() => {
        switch (kind) {
            case "area": return <AreaC data={data} pid={pid} animate={animate} />;
            case "line": return <LineC data={data} pid={pid} animate={animate} />;
            case "pie": return <PieC data={data} animate={animate} />;
            case "radar": return <RadarC data={data} animate={animate} />;
            default: return <BarC data={data} pid={pid} animate={animate} />;
        }
    })();

    return (
        // Outer card (surface color)
        <div >
            {/* Inner chart area (bg color + dot pattern lives here) */}
            <div style={{
                background: T.bg,
                borderRadius: 10,
                padding: "20px 16px 10px",
                border: `1px solid ${T.border}`,
                overflow: "hidden",
            }}>
                {(title || subtitle) && (
                    <div style={{ marginBottom: 12 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                            {title && (
                                <h3 style={{
                                    fontSize: 18, fontWeight: 800, color: T.text,
                                    margin: 0, letterSpacing: "-0.02em", lineHeight: 1.2,
                                }}>
                                    {title}
                                </h3>
                            )}
                            {["line", "area"].includes(kind) && <ChangeBadge data={data} />}
                        </div>
                        {subtitle && (
                            <p style={{ fontSize: 12, color: T.muted, margin: "4px 0 0", fontWeight: 400 }}>
                                {subtitle}
                            </p>
                        )}
                    </div>
                )}

                {chart}
            </div>
        </div>
    );
}