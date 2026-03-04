import { memo } from 'react';
import type { CompileStatus } from '../hooks/useTypstCompiler';

interface StatusBarProps {
  isCompiling: boolean;
  compileStatus: CompileStatus;
  fileName?: string;
  onExportPdf?: () => void;
}

export const StatusBar = memo(
  ({
    isCompiling,
    compileStatus,
    fileName = 'document.typ',
    onExportPdf,
  }: StatusBarProps) => {
    const renderStatus = () => {
      if (isCompiling) {
        return (
          <>
            <div
              style={{
                width: '12px',
                height: '12px',
                border: '2px solid #4ec9b0',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
              }}
            />
            <span>Compiling...</span>
          </>
        );
      }

      if (compileStatus === 'success') {
        return (
          <>
            <div
              style={{
                width: '8px',
                height: '8px',
                backgroundColor: '#4ec9b0',
                borderRadius: '50%',
              }}
            />
            <span>Compiled successfully</span>
          </>
        );
      }

      if (compileStatus === 'error') {
        return (
          <>
            <div
              style={{
                width: '8px',
                height: '8px',
                backgroundColor: '#f48771',
                borderRadius: '50%',
              }}
            />
            <span>Compilation error</span>
          </>
        );
      }

      return <span>Ready</span>;
    };

    return (
      <div
        style={{
          height: '32px',
          backgroundColor: '#252526',
          borderBottom: '1px solid #3e3e42',
          display: 'flex',
          alignItems: 'center',
          padding: '0 12px',
          fontSize: '12px',
          color: '#cccccc',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {renderStatus()}
        </div>
        <div style={{ color: '#858585' }}>|</div>
        <div>{fileName}</div>
        <div style={{ flex: 1 }} />
        {onExportPdf && (
          <button
            type="button"
            onClick={onExportPdf}
            disabled={compileStatus !== 'success'}
            style={{
              backgroundColor: 'transparent',
              border: '1px solid #3e3e42',
              borderRadius: '4px',
              color: compileStatus === 'success' ? '#cccccc' : '#666666',
              cursor: compileStatus === 'success' ? 'pointer' : 'not-allowed',
              padding: '2px 8px',
              fontSize: '11px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => {
              if (compileStatus === 'success')
                e.currentTarget.style.borderColor = '#4ec9b0';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = '#3e3e42';
            }}
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <title>Export PDF</title>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export PDF
          </button>
        )}
      </div>
    );
  }
);

StatusBar.displayName = 'StatusBar';
