'use client';

import { theme } from '../theme';

interface FileTabProps {
  fileName: string;
}

const FileIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
    <title>File</title>
    <path
      d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
      stroke={theme.heading}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <polyline
      points="14 2 14 8 20 8"
      stroke={theme.heading}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const FileTab = ({ fileName }: FileTabProps) => {
  return (
    <div
      style={{
        height: '32px',
        backgroundColor: theme.bgSidebar,
        borderBottom: `1px solid ${theme.border}`,
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <div
        style={{
          height: '100%',
          backgroundColor: theme.bg,
          borderBottom: `2px solid ${theme.function}`,
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          gap: '8px',
        }}
      >
        <FileIcon />
        <span style={{ fontSize: '13px', color: theme.text, fontWeight: 500 }}>
          {fileName}
        </span>
      </div>
    </div>
  );
};
