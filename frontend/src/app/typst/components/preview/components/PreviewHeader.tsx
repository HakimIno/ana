'use client';

import { memo } from 'react';
import { PdfUploader } from '../..';

interface PreviewHeaderProps {
  isCompiling: boolean;
  hasArtifact: boolean;
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  onSourceChange: (source: string) => void;
  onExportPdf?: () => void;
}

export const PreviewHeader = memo(
  ({
    isCompiling,
    hasArtifact,
    zoom,
    onZoomIn,
    onZoomOut,
    onResetZoom,
    onSourceChange,
    onExportPdf,
  }: PreviewHeaderProps) => {
    return (
      <div
        style={{
          height: '32px',
          backgroundColor: '#f3f3f3',
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 12px',
          fontSize: '12px',
          color: '#616161',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isCompiling && (
            <>
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  border: '2px solid #007acc',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                }}
              />
              <span>Compiling...</span>
            </>
          )}
          <PdfUploader onGenerated={onSourceChange} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {hasArtifact && <span style={{ color: '#858585' }}>01 of 01</span>}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#fff',
              border: '1px solid #d0d0d0',
              borderRadius: '4px',
              overflow: 'hidden',
            }}
          >
            <button
              type="button"
              onClick={onZoomOut}
              style={{
                padding: '4px 8px',
                border: 'none',
                borderRight: '1px solid #d0d0d0',
                backgroundColor: 'transparent',
                cursor: 'pointer',
                color: '#616161',
                fontSize: '14px',
                lineHeight: 1,
              }}
              title="Zoom Out"
            >
              −
            </button>
            <button
              type="button"
              onClick={onResetZoom}
              style={{
                padding: '4px 8px',
                border: 'none',
                borderRight: '1px solid #d0d0d0',
                backgroundColor: 'transparent',
                cursor: 'pointer',
                color: '#616161',
                fontSize: '11px',
                lineHeight: 1,
                minWidth: '50px',
              }}
              title="Reset to 100% or Fit Width"
            >
              {Math.round(zoom * 100)}%
            </button>
            <button
              type="button"
              onClick={onZoomIn}
              style={{
                padding: '4px 8px',
                border: 'none',
                backgroundColor: 'transparent',
                cursor: 'pointer',
                color: '#616161',
                fontSize: '14px',
                lineHeight: 1,
              }}
              title="Zoom In"
            >
              +
            </button>
          </div>
          {hasArtifact && onExportPdf && (
            <button
              type="button"
              onClick={onExportPdf}
              style={{
                padding: '4px 12px',
                backgroundColor: '#007acc',
                border: 'none',
                borderRadius: '3px',
                fontSize: '11px',
                color: '#fff',
                cursor: 'pointer',
                fontWeight: 500,
              }}
              title="Export as PDF"
            >
              Export PDF
            </button>
          )}
        </div>
      </div>
    );
  }
);

PreviewHeader.displayName = 'PreviewHeader';
