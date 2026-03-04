'use client';

import { memo, useMemo } from 'react';
import { editorFontStyles } from '../styles';
import { theme } from '../theme';

interface EditorHighlightProps {
  html: string;
  highlightRef: React.RefObject<HTMLPreElement | null>;
}

// Static style object - created once
const HIGHLIGHT_STYLE = {
  position: 'absolute' as const,
  inset: 0,
  margin: 0,
  padding: '12px',
  ...editorFontStyles,
  color: theme.text,
  backgroundColor: 'transparent',
  overflow: 'auto' as const,
  whiteSpace: 'pre' as const,
  wordWrap: 'normal' as const,
  pointerEvents: 'none' as const,
} as const;

export const EditorHighlight = memo(
  ({ html, highlightRef }: EditorHighlightProps) => {
    // Memoize innerHTML object to avoid recreation
    const dangerousHtml = useMemo(() => ({ __html: `${html}\n` }), [html]);

    return (
      <pre
        ref={highlightRef}
        aria-hidden="true"
        style={HIGHLIGHT_STYLE}
        // biome-ignore lint/security/noDangerouslySetInnerHtml: Required for syntax highlighting
        dangerouslySetInnerHTML={dangerousHtml}
      />
    );
  },
  // Only re-render when html changes
  (prevProps, nextProps) => prevProps.html === nextProps.html
);

EditorHighlight.displayName = 'EditorHighlight';
