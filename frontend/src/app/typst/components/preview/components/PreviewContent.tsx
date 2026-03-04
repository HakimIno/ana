'use client';

import { TypstDocument } from '@myriaddreamin/typst.react';
import { memo, useRef } from 'react';
import { DOCUMENT_FILL } from '../../../constants';
import { ErrorDisplay } from '../../ErrorDisplay';
import { LoadingDisplay } from '../../LoadingDisplay';
import { previewStyles } from '../styles';

interface PreviewContentProps {
  artifact: Uint8Array | null;
  error: string | null;
  zoom: number;
}

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

export const PreviewContent = memo(
  ({ artifact, error, zoom }: PreviewContentProps) => {
    // Use ref to track key changes for TypstDocument
    const artifactKeyRef = useRef(0);
    const lastArtifactRef = useRef<Uint8Array | null>(null);

    // Only increment key if artifact actually changed
    if (artifact && !areArtifactsEqual(artifact, lastArtifactRef.current)) {
      lastArtifactRef.current = artifact;
      artifactKeyRef.current += 1;
    } else if (!artifact) {
      lastArtifactRef.current = null;
    }

    if (error) {
      return <ErrorDisplay error={error} />;
    }

    if (artifact) {
      return (
        <div
          style={{
            // Use CSS zoom instead of transform for better quality
            zoom: zoom,
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <style>{previewStyles}</style>
          <TypstDocument
            key={artifactKeyRef.current}
            fill={DOCUMENT_FILL}
            artifact={artifact}
          />
        </div>
      );
    }

    return <LoadingDisplay />;
  },
  (prevProps: PreviewContentProps, nextProps: PreviewContentProps) => {
    if (prevProps.zoom !== nextProps.zoom) return false;
    if (prevProps.error !== nextProps.error) return false;
    return areArtifactsEqual(prevProps.artifact, nextProps.artifact);
  }
);

PreviewContent.displayName = 'PreviewContent';
