import { useCallback, useEffect, useRef } from 'react';

interface UseEditorScrollProps {
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}

export const useEditorScroll = ({ textareaRef }: UseEditorScrollProps) => {
  const highlightRef = useRef<HTMLPreElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const rafIdRef = useRef<number | null>(null);

  // Sync scroll between textarea, highlight layer, and line numbers
  // Use requestAnimationFrame for smoother performance
  const handleScroll = useCallback(() => {
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
    }

    rafIdRef.current = requestAnimationFrame(() => {
      const textarea = textareaRef.current;
      const highlight = highlightRef.current;
      const lineNumbers = lineNumbersRef.current;

      if (!textarea) return;

      if (highlight) {
        highlight.scrollTop = textarea.scrollTop;
        highlight.scrollLeft = textarea.scrollLeft;
      }
      if (lineNumbers) {
        lineNumbers.scrollTop = textarea.scrollTop;
      }

      rafIdRef.current = null;
    });
  }, [textareaRef]);

  // Attach scroll listener
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      textarea.removeEventListener('scroll', handleScroll);
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [handleScroll, textareaRef]);

  return {
    highlightRef,
    lineNumbersRef,
  };
};
