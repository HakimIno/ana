'use client';

import { memo, useCallback, useMemo, useState } from 'react';
import { Editor, Preview, ResizableSplit } from './components';
import { DEFAULT_TYPST_SOURCE } from './config';
import { useTypstCompiler } from './hooks/useTypstCompiler';
import { configureRenderer } from './lib/renderer-config';

// Configure renderer WASM once at module load
configureRenderer();

const TypstPage = memo(() => {
  const { onSourceChange, artifact, error, isCompiling, exportPdf } =
    useTypstCompiler({
      initialSource: DEFAULT_TYPST_SOURCE,
      debounceMs: 500,
    });

  // Track source generated externally (e.g. PDF upload) to push into Editor
  const [generatedSource, setGeneratedSource] = useState<string | undefined>(undefined);

  // Called by PdfUploader — update compiler AND push into Editor
  const handleGenerated = useCallback(
    (typstCode: string) => {
      setGeneratedSource(typstCode);
      onSourceChange(typstCode);
    },
    [onSourceChange]
  );

  // Memoize Editor props — only change when generated source or callbacks change
  const editorProps = useMemo(
    () => ({
      initialSource: DEFAULT_TYPST_SOURCE,
      onChange: onSourceChange,
      externalSource: generatedSource,
      fileName: 'main.typ',
    }),
    [onSourceChange, generatedSource]
  );

  // Memoize Preview props
  const previewProps = useMemo(
    () => ({
      artifact,
      error,
      isCompiling,
      onGenerated: handleGenerated,
      onExportPdf: exportPdf,
    }),
    [artifact, error, isCompiling, handleGenerated, exportPdf]
  );

  return (
    <div className="arc-shell font-sans antialiased">
      <div className="arc-window flex flex-col p-4 gap-4">
        {/* Editor & Preview Split */}
        <div className="flex-1 min-h-0 bg-gray-50/50 rounded-2xl border border-gray-100 overflow-hidden shadow-inner">
          <ResizableSplit
            left={<Editor {...editorProps} />}
            right={<Preview {...previewProps} />}
            style={{ flex: 1, height: '100%' }}
          />
        </div>
      </div>
    </div>
  );
});

TypstPage.displayName = 'TypstPage';

export default TypstPage;
