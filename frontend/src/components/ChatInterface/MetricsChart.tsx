"use client";

import { useState, useMemo } from "react";
import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';

interface ChartData {
    label: string;
    value: number;
    mom_growth_pct?: number;
}

interface MetricsChartProps {
    data: ChartData[];
    title?: string;
    type?: string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="custom-tooltip">
                <p className="tooltip-label">{label}</p>
                <div className="tooltip-items">
                    {payload.map((item: any, index: number) => (
                        <div key={index} className="tooltip-item">
                            <span className="dot-indicator" style={{ backgroundColor: item.color }}></span>
                            <span className="item-name">Value:</span>
                            <span className="item-value">
                                {item.value >= 1000 ? `${(item.value / 1000).toFixed(1)}k` : item.value.toLocaleString()}
                            </span>
                        </div>
                    ))}
                </div>
                <style jsx>{`
                    .custom-tooltip {
                        background: rgba(0, 0, 0, 0.9);
                        backdrop-filter: blur(8px);
                        border: 1px solid var(--glass-border);
                        padding: 10px 14px;
                        border-radius: 8px;
                        font-family: var(--font-sans);
                        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                    }
                    .tooltip-label {
                        font-size: 13px;
                        font-weight: 600;
                        color: #fff;
                        margin-bottom: 8px;
                    }
                    .tooltip-items {
                        display: flex;
                        flex-direction: column;
                        gap: 6px;
                    }
                    .tooltip-item {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 13px;
                    }
                    .dot-indicator {
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                    }
                    .item-name {
                        color: var(--text-secondary);
                    }
                    .item-value {
                        color: #fff;
                        font-weight: 600;
                        margin-left: auto;
                    }
                `}</style>
            </div>
        );
    }
    return null;
};

export default function MetricsChart({ data, title, type = 'area' }: MetricsChartProps) {
    const [selectedYear, setSelectedYear] = useState<string>("ALL");

    const years = useMemo(() => {
        const uniqueYears = new Set<string>();
        data.forEach(item => {
            const yearMatch = item.label.match(/\d{4}/);
            if (yearMatch) uniqueYears.add(yearMatch[0]);
        });
        const sorted = Array.from(uniqueYears).sort().reverse();
        return ["ALL", ...sorted];
    }, [data]);

    const filteredData = useMemo(() => {
        if (selectedYear === "ALL") return data;
        return data.filter(item => item.label.includes(selectedYear));
    }, [data, selectedYear]);

    if (!data || data.length === 0) return null;

    // Handle single data point elegantly
    if (data.length === 1) {
        const item = data[0];
        return (
            <div className="metrics-single-highlight glass-panel">
                <div className="highlight-content">
                    <span className="highlight-label">{item.label}</span>
                    <span className="highlight-value">
                        {item.value >= 1000 ? `${(item.value / 1000).toFixed(2)}k` : item.value.toLocaleString()}
                    </span>
                    <span className="highlight-status">SINGLE_POINT_DETECTION</span>
                </div>
                <style jsx>{`
                    .metrics-single-highlight {
                        padding: 24px;
                        margin-top: 12px;
                        display: flex;
                        justify-content: center;
                        border-left: 4px solid var(--accent-color);
                    }
                    .highlight-content {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        gap: 4px;
                    }
                    .highlight-label {
                        font-family: var(--font-mono);
                        font-size: 11px;
                        color: var(--text-secondary);
                        text-transform: uppercase;
                        letter-spacing: 0.1em;
                    }
                    .highlight-value {
                        font-family: var(--font-mono);
                        font-size: 36px;
                        font-weight: 700;
                        color: var(--accent-color);
                        text-shadow: 0 0 20px var(--accent-glow);
                    }
                    .highlight-status {
                        font-family: var(--font-mono);
                        font-size: 9px;
                        color: var(--terminal-green);
                        opacity: 0.8;
                    }
                `}</style>
            </div>
        );
    }

    const renderChart = () => {
        switch (type.toLowerCase()) {
            case 'bar':
                return (
                    <BarChart data={filteredData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.03)" />
                        <XAxis
                            dataKey="label"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
                            domain={['auto', 'auto']}
                            padding={{ top: 20, bottom: 10 }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                        <Bar
                            dataKey="value"
                            fill="var(--accent-color)"
                            radius={[4, 4, 0, 0]}
                            animationDuration={1500}
                        />
                    </BarChart>
                );
            case 'line':
                return (
                    <LineChart data={filteredData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.03)" />
                        <XAxis
                            dataKey="label"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
                            domain={['auto', 'auto']}
                            padding={{ top: 20, bottom: 10 }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border-color)', strokeWidth: 1 }} />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="var(--accent-color)"
                            strokeWidth={3}
                            dot={{ r: 4, fill: "var(--accent-color)", strokeWidth: 0 }}
                            activeDot={{ r: 6, stroke: "#fff", strokeWidth: 2 }}
                            animationDuration={1500}
                        />
                    </LineChart>
                );
            case 'area':
            default:
                return (
                    <AreaChart data={filteredData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                        <defs>
                            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--accent-color)" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.03)" />
                        <XAxis
                            dataKey="label"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
                            domain={['auto', 'auto']}
                            padding={{ top: 20, bottom: 10 }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border-color)', strokeWidth: 1 }} />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke="var(--accent-color)"
                            strokeWidth={3}
                            fill="url(#chartGradient)"
                            activeDot={{ r: 5, fill: "var(--accent-color)", stroke: "#fff", strokeWidth: 2 }}
                            animationDuration={1500}
                        />
                    </AreaChart>
                );
        }
    };

    // Calculate dynamic width for scrolling if data is dense
    // Reduced multiplier from 40 to 6 to bring points closer together
    const chartMinWidth = Math.max(100, filteredData.length * 6);

    return (
        <div className="metrics-chart-container glass-panel">
            <div className="chart-header">
                {title && <h4 className="chart-title">{title}</h4>}

                {years.length > 2 && (
                    <div className="year-selector">
                        {years.map(year => (
                            <button
                                key={year}
                                className={`year-btn ${selectedYear === year ? 'active' : ''}`}
                                onClick={() => setSelectedYear(year)}
                            >
                                {year}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="scroll-wrapper">
                <div style={{ width: `${chartMinWidth}%`, height: 220, minWidth: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        {renderChart()}
                    </ResponsiveContainer>
                </div>
            </div>

            <style jsx>{`
                .metrics-chart-container {
                    padding: 14px;
                    margin: 8px 0;
                    border-radius: 12px;
                    background: rgba(255, 255, 255, 0.02);
                }

                .chart-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 12px;
                    gap: 16px;
                    flex-wrap: wrap;
                }

                .chart-title {
                    font-family: var(--font-mono);
                    font-size: 11px;
                    font-weight: 700;
                    color: var(--text-primary);
                    letter-spacing: 0.1em;
                    text-transform: uppercase;
                    margin: 0;
                }

                .year-selector {
                    display: flex;
                    gap: 6px;
                    background: rgba(255, 255, 255, 0.05);
                    padding: 3px;
                    border-radius: 8px;
                    border: 1px solid var(--border-color);
                }

                .year-btn {
                    background: transparent;
                    border: none;
                    color: var(--text-secondary);
                    font-family: var(--font-mono);
                    font-size: 10px;
                    padding: 4px 10px;
                    cursor: pointer;
                    border-radius: 6px;
                    transition: all 0.2s;
                }

                .year-btn:hover {
                    color: var(--text-primary);
                    background: rgba(255, 255, 255, 0.05);
                }

                .year-btn.active {
                    background: var(--accent-color);
                    color: white;
                    box-shadow: 0 0 12px var(--accent-glow);
                }

                .scroll-wrapper {
                    overflow-x: auto;
                    overflow-y: hidden;
                    width: 100%;
                    padding-bottom: 10px;
                }

                .scroll-wrapper::-webkit-scrollbar {
                    height: 4px;
                }

                .scroll-wrapper::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                }

                .scroll-wrapper::-webkit-scrollbar-thumb:hover {
                    background: var(--accent-color);
                }
            `}</style>
        </div>
    );
}
