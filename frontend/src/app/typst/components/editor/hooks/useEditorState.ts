import {
  startTransition,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { highlightSource } from '../lib';
import type { EditorState } from '../types';
import { getLineNumber } from '../utils';

interface UseEditorStateProps {
  initialSource: string;
  onChange: (source: string) => void;
}

export const useEditorState = ({
  initialSource,
  onChange,
}: UseEditorStateProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Internal source state - Editor is uncontrolled
  const [source, setSourceInternal] = useState(initialSource);
  const sourceRef = useRef(source);

  // UI state
  const [activeLineIndex, setActiveLineIndex] = useState(0);
  const [highlightedHtml, setHighlightedHtml] = useState(() =>
    highlightSource(initialSource)
  );

  // Refs for scheduling
  const highlightRafRef = useRef<number | null>(null);
  const onChangeRafRef = useRef<number | null>(null);
  const lastHighlightedSourceRef = useRef<string>(initialSource);
  const pendingSourceRef = useRef<string | null>(null);

  // Keep source ref in sync (synchronous)
  sourceRef.current = source;

  // Memoize line count
  const lineCount = useMemo(() => source.split('\n').length, [source]);

  // Syntax highlighting using requestAnimationFrame for smoother updates
  useEffect(() => {
    // Skip if source hasn't changed
    if (lastHighlightedSourceRef.current === source) {
      return;
    }

    // Cancel pending highlight
    if (highlightRafRef.current !== null) {
      cancelAnimationFrame(highlightRafRef.current);
    }

    // Schedule highlighting on next frame
    highlightRafRef.current = requestAnimationFrame(() => {
      lastHighlightedSourceRef.current = source;
      startTransition(() => {
        setHighlightedHtml(highlightSource(source));
      });
      highlightRafRef.current = null;
    });

    return () => {
      if (highlightRafRef.current !== null) {
        cancelAnimationFrame(highlightRafRef.current);
      }
    };
  }, [source]);

  // Stable setSource - immediate state update, debounced parent notification
  const setSource = useCallback(
    (newSource: string) => {
      // Update internal state immediately for responsive typing
      setSourceInternal(newSource);

      // Store pending source for parent notification
      pendingSourceRef.current = newSource;

      // Cancel pending onChange
      if (onChangeRafRef.current !== null) {
        cancelAnimationFrame(onChangeRafRef.current);
      }

      // Notify parent on next frame (batches rapid changes)
      onChangeRafRef.current = requestAnimationFrame(() => {
        if (pendingSourceRef.current !== null) {
          onChange(pendingSourceRef.current);
          pendingSourceRef.current = null;
        }
        onChangeRafRef.current = null;
      });
    },
    [onChange]
  );

  // Track cursor position for active line with RAF debounce
  const cursorRafRef = useRef<number | null>(null);
  const lastLineIndexRef = useRef(0);

  const handleCursorChange = useCallback(() => {
    // Cancel pending cursor update
    if (cursorRafRef.current !== null) {
      cancelAnimationFrame(cursorRafRef.current);
    }

    cursorRafRef.current = requestAnimationFrame(() => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      const cursorPos = textarea.selectionStart;
      const lineIndex = getLineNumber(sourceRef.current, cursorPos);

      // Only update state if line actually changed
      if (lineIndex !== lastLineIndexRef.current) {
        lastLineIndexRef.current = lineIndex;
        setActiveLineIndex(lineIndex);
      }

      cursorRafRef.current = null;
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (highlightRafRef.current !== null) {
        cancelAnimationFrame(highlightRafRef.current);
      }
      if (onChangeRafRef.current !== null) {
        cancelAnimationFrame(onChangeRafRef.current);
      }
      if (cursorRafRef.current !== null) {
        cancelAnimationFrame(cursorRafRef.current);
      }
    };
  }, []);

  // Get current editor state
  const getState = useCallback((): EditorState => {
    const textarea = textareaRef.current;
    return {
      source: sourceRef.current,
      selectionStart: textarea?.selectionStart ?? 0,
      selectionEnd: textarea?.selectionEnd ?? 0,
    };
  }, []);

  return {
    textareaRef,
    source,
    setSource,
    activeLineIndex,
    highlightedHtml,
    lineCount,
    handleCursorChange,
    getState,
  };
};
