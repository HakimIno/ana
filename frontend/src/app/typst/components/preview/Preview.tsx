'use client';

import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { PreviewContent } from './components/PreviewContent';
import { PreviewHeader } from './components/PreviewHeader';
import { containerStyles, contentStyles } from './styles';
import type { PreviewProps } from './types';

// Helper to compare Uint8Array efficiently
const areArtifactsEqual = (
  a: Uint8Array | null,
  b: Uint8Array | null
): boolean => {
  if (a === b) return true;
  if (!a || !b) return false;
  if (a.length !== b.length) return false;

  // Sample comparison for large arrays (faster than full comparison)
  const sampleSize = Math.min(100, a.length);
  const step = Math.max(1, Math.floor(a.length / sampleSize));

  for (let i = 0; i < a.length; i += step) {
    if (a[i] !== b[i]) return false;
  }

  return true;
};

export const Preview = memo(
  ({ artifact, error, isCompiling, onGenerated, onExportPdf }: PreviewProps) => {
    const contentRef = useRef<HTMLDivElement>(null);
    const rafIdRef = useRef<number | null>(null);

    // Fix Typst document container height when artifact changes
    useEffect(() => {
      if (!artifact) return;

      // Cancel any pending RAF
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }

      // Use requestAnimationFrame for better performance
      rafIdRef.current = requestAnimationFrame(() => {
        const typstApp =
          contentRef.current?.querySelector<HTMLElement>('.typst-app');
        if (typstApp) {
          typstApp.style.height = 'auto';
          typstApp.style.minHeight = '100%';
        }
        rafIdRef.current = null;
      });

      return () => {
        if (rafIdRef.current !== null) {
          cancelAnimationFrame(rafIdRef.current);
        }
      };
    }, [artifact]);

    const [zoom, setZoom] = useState(1);

    // Memoize hasArtifact to avoid recreation
    const hasArtifact = !!artifact;

    // Zoom handlers
    const handleZoomIn = useCallback(() => {
      setZoom((prev: number) => Math.min(prev * 1.2, 5));
    }, []);

    const handleZoomOut = useCallback(() => {
      setZoom((prev: number) => Math.max(prev / 1.2, 0.2));
    }, []);

    const handleResetZoom = useCallback(() => {
      setZoom(1);
    }, []);

    return (
      <div style={containerStyles}>
        <PreviewHeader
          isCompiling={isCompiling}
          hasArtifact={hasArtifact}
          zoom={zoom}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onResetZoom={handleResetZoom}
          onSourceChange={onGenerated}
          onExportPdf={onExportPdf}
        />
        <div
          ref={contentRef}
          className="preview-container"
          style={contentStyles}
        >
          <PreviewContent artifact={artifact} error={error} zoom={zoom} />
        </div>
      </div>
    );
  },
  // Custom comparison to avoid re-renders when artifact content is same
  (prevProps: PreviewProps, nextProps: PreviewProps) => {
    if (prevProps.isCompiling !== nextProps.isCompiling) return false;
    if (prevProps.error !== nextProps.error) return false;
    return areArtifactsEqual(prevProps.artifact, nextProps.artifact);
  }
);

Preview.displayName = 'Preview';
