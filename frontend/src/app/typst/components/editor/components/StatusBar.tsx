'use client';

import { theme } from '../theme';

interface StatusBarProps {
  lineNumber: number;
}

export const StatusBar = ({ lineNumber }: StatusBarProps) => {
  return (
    <div
      style={{
        height: '22px',
        backgroundColor: theme.bgSidebar,
        borderTop: `1px solid ${theme.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        padding: '0 12px',
        gap: '16px',
        fontSize: '11px',
        color: theme.lineNumber,
      }}
    >
      <span>Ln {lineNumber}</span>
      <span>UTF-8</span>
      <span style={{ color: theme.heading }}>Typst</span>
    </div>
  );
};
