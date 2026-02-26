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

// ─── Palette (evilcharts-style) ─────────────────────────────────────────────
const COLORS = [
    "#0d9488", // teal-600
    "#f97316", // orange-500
    "#eab308", // yellow-500
    "#14b8a6", // teal-400
    "#6366f1", // indigo-500
    "#ec4899", // pink-500
    "#3b82f6", // blue-500
    "#10b981", // emerald-500
];

// ─── Smart chart-type pick ──────────────────────────────────────────────────
type ChartKind = "bar" | "area" | "line" | "pie" | "radar";

function pickType(hint: string, data: Datum[]): ChartKind {
    const t = (hint || "").toLowerCase();
    if (["pie", "donut", "ring", "proportion"].includes(t)) return "pie";
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

// ─── Normalise data ─────────────────────────────────────────────────────────
interface RawItem { [k: string]: any; }
interface Datum { label: string; value: number;[k: string]: any; }

function normalise(raw: RawItem[]): Datum[] {
    if (!raw?.length) return [];
    return raw.map(item => {
        const label =
            item.label ?? item.name ?? item.branch ?? item.category ??
            item.month ?? item.year ?? item.date ?? item.period ??
            item.dept ?? item.department ?? item.product ?? item.type ??
            item.region ?? item.item ??
            (() => { const k = Object.keys(item).find(k => typeof item[k] === "string"); return k ? item[k] : "—"; })();

        const value =
            item.value ?? item.count ?? item.total ?? item.revenue ??
            item.score ?? item.amount ?? item.avg ?? item.average ??
            item.salary ?? item.sales ?? item.profit ?? item.cost ??
            (() => { const k = Object.keys(item).find(k => typeof item[k] === "number"); return k ? item[k] : 0; })();

        return { ...item, label: String(label), value: Number(value) };
    });
}

// ─── Helpers ────────────────────────────────────────────────────────────────
const fmt = (v: number) =>
    v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M`
        : v >= 1000 ? `${(v / 1000).toFixed(1)}k`
            : v.toLocaleString();

const truncLabel = (s: string, max = 14) =>
    s.length > max ? s.slice(0, max) + "…" : s;

// ─── Dot grid ───────────────────────────────────────────────────────────────
const DotGrid = ({ id }: { id: string }) => (
    <defs>
        <pattern id={id} x={0} y={0} width={16} height={16} patternUnits="userSpaceOnUse">
            <circle cx={8} cy={8} r={0.7} fill="rgba(0,0,0,0.05)" />
        </pattern>
    </defs>
);

// ─── Tooltip ────────────────────────────────────────────────────────────────
const Tip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
        <div style={{
            background: "#fff",
            border: "1px solid rgba(0,0,0,0.06)",
            borderRadius: 10,
            padding: "8px 14px",
            boxShadow: "0 4px 14px rgba(0,0,0,0.06)",
            fontSize: 13,
            fontFamily: "var(--font-sans, sans-serif)",
        }}>
            <div style={{ color: "#aaa", fontWeight: 600, marginBottom: 3, fontSize: 10 }}>
                {label || payload[0]?.payload?.label}
            </div>
            {payload.map((p: any, i: number) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 1 }}>
                    <span style={{ width: 7, height: 7, borderRadius: "50%", background: p.fill || p.stroke || p.color, display: "inline-block" }} />
                    <span style={{ color: "#222", fontWeight: 700 }}>{fmt(p.value)}</span>
                </div>
            ))}
        </div>
    );
};

// ─── Axis / Grid ────────────────────────────────────────────────────────────
const axisX = { fill: "#bbb", fontSize: 10, fontWeight: 500 };
const axisY = { fill: "#bbb", fontSize: 10 };
const gridClr = "rgba(0,0,0,0.04)";

// ─── Pie label renderer (value on slice) ────────────────────────────────────
const RADIAN = Math.PI / 180;
const renderPieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, value }: any) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    return (
        <text
            x={x} y={y}
            fill="#fff"
            textAnchor="middle"
            dominantBaseline="central"
            style={{ fontSize: 12, fontWeight: 700, textShadow: "0 1px 3px rgba(0,0,0,0.3)" }}
        >
            {fmt(value)}
        </text>
    );
};

// ─── Chart Sub-Components (top-level to avoid remount) ─────────────────────
interface ChartSubProps { data: Datum[]; pid: string; animate: boolean; }

function BarC({ data, pid, animate }: ChartSubProps) {
    return (
        <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} margin={{ top: 4, right: 8, left: -6, bottom: 2 }} barCategoryGap="28%">
                <DotGrid id={pid} />
                <rect width="100%" height="100%" fill={`url(#${pid})`} />
                <CartesianGrid vertical={false} stroke={gridClr} />
                <XAxis
                    dataKey="label" axisLine={false} tickLine={false}
                    tick={axisX} dy={6}
                    tickFormatter={(v: string) => truncLabel(v)}
                    interval={data.length > 12 ? Math.ceil(data.length / 8) : 0}
                />
                <YAxis axisLine={false} tickLine={false} tick={axisY} tickFormatter={fmt} width={40} />
                <Tooltip content={<Tip />} cursor={{ fill: "rgba(0,0,0,0.02)" }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive={animate} animationDuration={700}>
                    {data.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
}

function AreaC({ data, pid, animate }: ChartSubProps) {
    const c = COLORS[0];
    const gid = `${pid}-ag`;
    return (
        <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data} margin={{ top: 4, right: 8, left: -6, bottom: 2 }}>
                <defs>
                    <DotGrid id={pid} />
                    <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={c} stopOpacity={0.12} />
                        <stop offset="100%" stopColor={c} stopOpacity={0} />
                    </linearGradient>
                </defs>
                <rect width="100%" height="100%" fill={`url(#${pid})`} />
                <CartesianGrid vertical={false} stroke={gridClr} />
                <XAxis
                    dataKey="label" axisLine={false} tickLine={false}
                    tick={axisX} dy={6}
                    tickFormatter={(v: string) => truncLabel(v)}
                    interval={data.length > 12 ? Math.ceil(data.length / 8) : 0}
                />
                <YAxis axisLine={false} tickLine={false} tick={axisY} tickFormatter={fmt} width={40} />
                <Tooltip content={<Tip />} />
                <Area
                    type="monotone" dataKey="value"
                    stroke={c} strokeWidth={2}
                    fill={`url(#${gid})`}
                    dot={false}
                    activeDot={{ r: 4, fill: c, stroke: "#fff", strokeWidth: 2 }}
                    isAnimationActive={animate} animationDuration={800}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
}

function LineC({ data, pid, animate }: ChartSubProps) {
    const c = COLORS[4]; // indigo
    return (
        <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data} margin={{ top: 4, right: 8, left: -6, bottom: 2 }}>
                <DotGrid id={pid} />
                <rect width="100%" height="100%" fill={`url(#${pid})`} />
                <CartesianGrid vertical={false} stroke={gridClr} />
                <XAxis
                    dataKey="label" axisLine={false} tickLine={false}
                    tick={axisX} dy={6}
                    tickFormatter={(v: string) => truncLabel(v)}
                    interval={data.length > 12 ? Math.ceil(data.length / 8) : 0}
                />
                <YAxis axisLine={false} tickLine={false} tick={axisY} tickFormatter={fmt} width={40} />
                <Tooltip content={<Tip />} />
                <Line
                    type="monotone" dataKey="value"
                    stroke={c} strokeWidth={2}
                    dot={{ r: 3, fill: "#fff", stroke: c, strokeWidth: 1.5 }}
                    activeDot={{ r: 5, fill: c, stroke: "#fff", strokeWidth: 2 }}
                    isAnimationActive={animate} animationDuration={800}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}

function PieC({ data, animate }: Omit<ChartSubProps, 'pid'>) {
    return (
        <ResponsiveContainer width="100%" height={260}>
            <PieChart>
                <Pie
                    data={data} cx="50%" cy="48%"
                    innerRadius={0} outerRadius={100}
                    dataKey="value" nameKey="label"
                    paddingAngle={2}
                    cornerRadius={4}
                    isAnimationActive={animate} animationDuration={700}
                    stroke="#fff"
                    strokeWidth={3}
                    label={renderPieLabel}
                    labelLine={false}
                >
                    {data.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip content={<Tip />} />
                <Legend
                    iconType="circle" iconSize={8}
                    wrapperStyle={{ paddingTop: 8 }}
                    formatter={(v: any) => (
                        <span style={{ color: "#555", fontSize: 11, fontWeight: 500 }}>{v}</span>
                    )}
                />
            </PieChart>
        </ResponsiveContainer>
    );
}

function RadarC({ data, animate }: Omit<ChartSubProps, 'pid'>) {
    const c = COLORS[0]; // teal
    return (
        <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 24 }}>
                <PolarGrid stroke="rgba(0,0,0,0.06)" />
                <PolarAngleAxis dataKey="label" tick={{ fill: "#888", fontSize: 10, fontWeight: 500 }} />
                <PolarRadiusAxis tick={false} axisLine={false} />
                <Radar
                    dataKey="value"
                    fill={c} fillOpacity={0.12}
                    stroke={c} strokeWidth={2}
                    isAnimationActive={animate} animationDuration={800}
                />
                <Tooltip content={<Tip />} />
            </RadarChart>
        </ResponsiveContainer>
    );
}

// ─── Component ──────────────────────────────────────────────────────────────
interface Props { data: RawItem[]; title?: string; type?: string; }

export default function MetricsChart({ data: raw, title, type = "bar" }: Props) {
    const data = useMemo(() => normalise(raw), [raw]);
    const kind = useMemo(() => pickType(type, data), [type, data]);

    // Animate once on mount only
    const mounted = useRef(false);
    const [animate, setAnimate] = useState(true);
    useEffect(() => {
        if (!mounted.current) {
            mounted.current = true;
            const t = setTimeout(() => setAnimate(false), 1200);
            return () => clearTimeout(t);
        }
    }, []);

    if (!data.length) return null;

    const pid = useMemo(() => `p${Math.random().toString(36).slice(2, 7)}`, []);

    // ═══════════════════════════════════════════════════════════════════════
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
        <div style={{
            background: "#fff",
            border: "1px solid rgba(0,0,0,0.07)",
            borderRadius: 14,
            padding: "20px 18px 10px",
        }}>
            {title && (
                <h3 style={{
                    fontSize: 14,
                    fontWeight: 700,
                    color: "#222",
                    margin: "0 0 4px 0",
                    fontFamily: "var(--font-sans, sans-serif)",
                }}>
                    {title}
                </h3>
            )}
            {chart}
        </div>
    );
}
