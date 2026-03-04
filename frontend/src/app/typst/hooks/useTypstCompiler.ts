import { useCallback, useEffect, useRef, useState } from 'react';
import { DOCUMENT_PATH } from '../constants';
import { COMPILER_CONFIG, generateTypstPreamble } from '../lib/compiler-config';
import { getCompiler } from '../lib/typst-compiler';

export type CompileStatus = 'idle' | 'compiling' | 'success' | 'error';

export interface UseTypstCompilerOptions {
  initialSource: string;
  debounceMs?: number;
}

export interface UseTypstCompilerReturn {
  sourceRef: React.MutableRefObject<string>;
  onSourceChange: (source: string) => void;
  artifact: Uint8Array | null;
  error: string | null;
  isCompiling: boolean;
  compileStatus: CompileStatus;
  exportPdf: () => Promise<void>;
}

/**
 * Custom hook for Typst compilation
 * Optimized to avoid unnecessary re-renders
 */
export const useTypstCompiler = ({
  initialSource,
  debounceMs = COMPILER_CONFIG.debounceMs,
}: UseTypstCompilerOptions): UseTypstCompilerReturn => {
  // Use ref for source to avoid re-renders on every keystroke
  const sourceRef = useRef(initialSource);

  // Only these trigger re-renders (compilation results)
  const [artifact, setArtifact] = useState<Uint8Array | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [compileStatus, setCompileStatus] = useState<CompileStatus>('idle');

  const compilerReadyRef = useRef(false);
  const compileTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isCompilingRef = useRef(false);

  // Compile function stored in ref
  const compileTypst = useCallback(async (typstSource: string) => {
    // Prevent concurrent compilations
    if (isCompilingRef.current) return;
    isCompilingRef.current = true;

    setIsCompiling(true);
    setCompileStatus('compiling');
    setError(null);

    try {
      const compiler = await getCompiler();
      compilerReadyRef.current = true;

      await compiler.reset();

      // Combine preamble with user source
      const preamble = generateTypstPreamble();
      const fullSource = `${preamble}\n${typstSource}`;
      await compiler.addSource(DOCUMENT_PATH, fullSource);

      const result = await compiler.compile({
        mainFilePath: DOCUMENT_PATH,
      });

      if (result.result) {
        setArtifact(result.result);
        setCompileStatus('success');
        setError(null);
      } else if (result.diagnostics) {
        const errorMsg = JSON.stringify(result.diagnostics, null, 2);
        setError(errorMsg);
        setCompileStatus('error');
      } else {
        setError('Compilation failed: no result returned');
        setCompileStatus('error');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      setCompileStatus('error');
    } finally {
      setIsCompiling(false);
      isCompilingRef.current = false;
    }
  }, []);

  // Initial compile
  useEffect(() => {
    compileTypst(initialSource);
  }, [compileTypst, initialSource]);

  // Stable source change handler that triggers debounced compilation
  const onSourceChange = useCallback(
    (newSource: string) => {
      sourceRef.current = newSource;

      if (!compilerReadyRef.current) return;

      // Clear existing timeout
      if (compileTimeoutRef.current) {
        clearTimeout(compileTimeoutRef.current);
      }

      // Debounce compilation
      compileTimeoutRef.current = setTimeout(() => {
        compileTypst(sourceRef.current);
      }, debounceMs);
    },
    [compileTypst, debounceMs]
  );

  const exportPdf = useCallback(async () => {
    try {
      const compiler = await getCompiler();
      const result = await compiler.exportPdf({
        mainFilePath: DOCUMENT_PATH,
      });

      if (result.result) {
        const blob = new Blob([new Uint8Array(result.result)], {
          type: 'application/pdf',
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'document.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } else {
        setError('Failed to export PDF: No result returned');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (compileTimeoutRef.current) {
        clearTimeout(compileTimeoutRef.current);
      }
    };
  }, []);

  return {
    sourceRef,
    onSourceChange,
    artifact,
    error,
    isCompiling,
    compileStatus,
    exportPdf,
  };
};
