import { memo } from 'react';

interface ErrorDisplayProps {
  error: string;
}

export const ErrorDisplay = memo(({ error }: ErrorDisplayProps) => (
  <div
    style={{
      padding: '20px',
      backgroundColor: '#fff5f5',
      border: '1px solid #feb2b2',
      borderRadius: '4px',
      margin: '20px',
    }}
  >
    <h3
      style={{
        color: '#c53030',
        marginTop: 0,
        marginBottom: '12px',
        fontSize: '16px',
        fontWeight: 600,
      }}
    >
      Compilation Error:
    </h3>
    <pre
      style={{
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        color: '#742a2a',
        fontFamily: 'Consolas, "Courier New", monospace',
        fontSize: '13px',
        lineHeight: '1.5',
        margin: 0,
        overflow: 'auto',
      }}
    >
      {error}
    </pre>
  </div>
));

ErrorDisplay.displayName = 'ErrorDisplay';
