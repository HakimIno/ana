'use client';

import { memo, useMemo } from 'react';
import { Editor, Preview, ResizableSplit } from './components';
import { DEFAULT_TYPST_SOURCE } from './config';
import { useTypstCompiler } from './hooks/useTypstCompiler';
import { configureRenderer } from './lib/renderer-config';

// Configure renderer WASM once at module load
configureRenderer();

// Static styles - defined outside component to avoid recreation
const CONTAINER_STYLE = {
  width: '100%',
  height: '100vh',
  display: 'flex',
  flexDirection: 'column' as const,
  fontFamily: 'system-ui, -apple-system, sans-serif',
  padding: '12px',
} as const;

const TypstPage = memo(() => {
  const { onSourceChange, artifact, error, isCompiling, exportPdf } =
    useTypstCompiler({
      initialSource: DEFAULT_TYPST_SOURCE,
      debounceMs: 500,
    });

  // Memoize Editor props that shouldn't change
  const editorProps = useMemo(
    () => ({
      initialSource: DEFAULT_TYPST_SOURCE,
      onChange: onSourceChange,
      fileName: 'main.typ',
    }),
    [onSourceChange]
  );

  // Memoize Preview props
  const previewProps = useMemo(
    () => ({
      artifact,
      error,
      isCompiling,
      onExportPdf: exportPdf,
    }),
    [artifact, error, isCompiling, exportPdf]
  );

  return (
    <div style={CONTAINER_STYLE} className="bg-primary">
      <ResizableSplit
        left={<Editor {...editorProps} />}
        right={<Preview {...previewProps} />}
        style={{ flex: 1 }}
      />
    </div>
  );
});

TypstPage.displayName = 'TypstPage';

export default TypstPage;
