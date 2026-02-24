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
        <div className="analysis-table-container">
            <div className="table-header-meta">
                <Table size={12} /> STRUCTURED_REPORT
            </div>
            <div className="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            {data.headers.map((header, i) => (
                                <th key={i}>{header}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.rows.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                                {row.map((cell, cellIndex) => (
                                    <td key={cellIndex}>
                                        {typeof cell === 'number' ? cell.toLocaleString() : cell}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AnalysisTable;
