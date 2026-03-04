import React from 'react';
import { Table } from 'lucide-react';

interface AnalysisTableProps {
    data: {
        headers: string[];
        rows: (string | number)[][];
    };
}

const AnalysisTable: React.FC<AnalysisTableProps> = ({ data }) => {
    if (!data || !data.headers || !data.rows) return null;

    return (
        <div style={{
            marginTop: '24px',
            marginBottom: '16px',
            background: '#ffffff',
            border: '1px solid rgba(0, 0, 0, 0.08)',
            borderRadius: '16px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.03)',
            overflow: 'hidden',
            fontFamily: 'var(--font-sans)',
        }}>
            <div style={{
                padding: '12px 16px',
                background: '#fafafa',
                borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '11px',
                fontWeight: 700,
                color: '#666',
                letterSpacing: '0.05em',
            }}>
                <Table size={14} style={{ color: '#000' }} /> SUMMARY_DATA_MATRIX
            </div>
            <div style={{ overflowX: 'auto', padding: '0 4px 4px 4px' }}>
                <table style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '13.5px',
                    textAlign: 'left',
                }}>
                    <thead>
                        <tr>
                            {data.headers.map((header, i) => (
                                <th key={i} style={{
                                    padding: '12px 16px',
                                    fontWeight: 700,
                                    color: '#111',
                                    whiteSpace: 'nowrap',
                                    borderBottom: '2px solid rgba(0,0,0,0.08)'
                                }}>{header}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.rows.map((row, rowIndex) => (
                            <tr key={rowIndex} style={{
                                transition: 'background-color 0.2s ease',
                                borderBottom: rowIndex === data.rows.length - 1 ? 'none' : '1px solid rgba(0,0,0,0.04)'
                            }}
                                onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.02)'}
                                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                            >
                                {row.map((cell, cellIndex) => {
                                    const isNumber = typeof cell === 'number';
                                    const cValue = isNumber ? new Intl.NumberFormat().format(cell as number) : cell;
                                    return (
                                        <td key={cellIndex} style={{
                                            padding: '12px 16px',
                                            color: '#333',
                                            fontWeight: isNumber ? 500 : 400,
                                            fontFeatureSettings: isNumber ? '"tnum"' : 'normal'
                                        }}>
                                            {cValue}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AnalysisTable;
