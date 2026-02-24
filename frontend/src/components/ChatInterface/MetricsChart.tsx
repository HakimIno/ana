"use client";

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
                            <span className="item-name">Revenue:</span>
                            <span className="item-value">
                                {item.value >= 1000 ? `${(item.value / 1000).toFixed(1)}k` : item.value}
                            </span>
                        </div>
                    ))}
                </div>
                <style jsx>{`
                    .custom-tooltip {
                        background: #000;
                        border: 1px solid var(--border-color);
                        padding: 10px 14px;
                        border-radius: 6px;
                        font-family: var(--font-mono);
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
                        border-radius: 2px;
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
    if (!data || data.length === 0) return null;

    // Handle single data point elegantly
    if (data.length === 1) {
        const item = data[0];
        return (
            <div className="metrics-single-highlight">
                <div className="highlight-content">
                    <span className="highlight-label">{item.label}</span>
                    <span className="highlight-value">
                        {item.value >= 1000 ? `${(item.value / 1000).toFixed(2)}k` : item.value.toLocaleString()}
                    </span>
                    <span className="highlight-sub">PRIMARY_METRIC_MATCH</span>
                </div>
                <style jsx>{`
                    .metrics-single-highlight {
                        padding: 24px;
                        background: #0a0a0a;
                        border: 1px solid var(--border-color);
                        border-radius: 4px;
                        margin-top: 12px;
                        display: flex;
                        justify-content: center;
                        border-left: 2px solid var(--accent-color);
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
                        font-size: 32px;
                        font-weight: 700;
                        color: var(--accent-color);
                    }
                    .highlight-sub {
                        font-family: var(--font-mono);
                        font-size: 9px;
                        color: var(--text-secondary);
                        opacity: 0.5;
                    }
                `}</style>
            </div>
        );
    }

    const renderChart = () => {
        switch (type.toLowerCase()) {
            case 'bar':
                return (
                    <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.03)" />
                        <XAxis
                            dataKey="label"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
                            domain={['auto', 'auto']}
                            padding={{ top: 20, bottom: 10 }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                        <Bar
                            dataKey="value"
                            fill="var(--accent-color)"
                            radius={[2, 2, 0, 0]}
                            animationDuration={1000}
                        />
                    </BarChart>
                );
            case 'line':
                return (
                    <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.03)" />
                        <XAxis
                            dataKey="label"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
                            domain={['auto', 'auto']}
                            padding={{ top: 20, bottom: 10 }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border-color)', strokeWidth: 1 }} />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="var(--accent-color)"
                            strokeWidth={2}
                            dot={{ r: 3, fill: "var(--accent-color)", strokeWidth: 0 }}
                            activeDot={{ r: 5, stroke: "#fff", strokeWidth: 2 }}
                            animationDuration={1000}
                        />
                    </LineChart>
                );
            case 'area':
            default:
                return (
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--accent-color)" stopOpacity={0.15} />
                                <stop offset="95%" stopColor="var(--accent-color)" stopOpacity={0} />
                            </linearGradient>
                            <pattern id="dotPattern" x="0" y="0" width="10" height="10" patternUnits="userSpaceOnUse">
                                <circle cx="1.5" cy="1.5" r="1.5" fill="var(--accent-color)" fillOpacity="0.25" />
                            </pattern>
                        </defs>
                        <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.03)" />
                        <XAxis
                            dataKey="label"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
                            domain={['auto', 'auto']}
                            padding={{ top: 20, bottom: 10 }}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border-color)', strokeWidth: 1 }} />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke="var(--accent-color)"
                            strokeWidth={2}
                            fill="url(#dotPattern)"
                            activeDot={{ r: 4, fill: "var(--accent-color)", stroke: "#fff", strokeWidth: 2 }}
                            animationDuration={1000}
                        />
                    </AreaChart>
                );
        }
    };

    return (
        <div className="metrics-chart-container">
            {title && <h4 className="chart-title">{title}</h4>}
            <div style={{ width: '100%', height: 180 }}>
                <ResponsiveContainer>
                    {renderChart()}
                </ResponsiveContainer>
            </div>

            <style jsx>{`
        .metrics-chart-container {
          padding: 12px 0;
          position: relative;
        }

        .chart-title {
          font-family: var(--font-mono);
          font-size: 10px;
          font-weight: 600;
          color: var(--accent-color);
          margin-bottom: 20px;
          letter-spacing: 0.1em;
          text-transform: uppercase;
        }
      `}</style>
        </div>
    );
}
