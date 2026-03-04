'use client';

import { memo, useMemo } from 'react';
import { EditorHighlight } from './components/EditorHighlight';
import { EditorLineNumbersContainer } from './components/EditorLineNumbersContainer';
import { EditorTextarea } from './components/EditorTextarea';
import { FileTab } from './components/FileTab';
import { StatusBar } from './components/StatusBar';
import { useEditorKeyboard } from './hooks/useEditorKeyboard';
import { useEditorScroll } from './hooks/useEditorScroll';
import { useEditorState } from './hooks/useEditorState';
import { editorStyles } from './styles';
import { theme } from './theme';
import type { EditorProps } from './types';

// Static styles - defined outside component to avoid recreation
const EDITOR_CONTAINER_STYLE = {
  width: '100%',
  height: '100%',
  display: 'flex',
  flexDirection: 'column' as const,
  backgroundColor: theme.bg,
  borderRight: `1px solid ${theme.border}`,
  borderRadius: '12px',
  overflow: 'hidden' as const,
} as const;

const EDITOR_CONTENT_STYLE = {
  flex: 1,
  display: 'flex',
  overflow: 'hidden' as const,
} as const;

const EDITOR_TEXTAREA_CONTAINER_STYLE = {
  flex: 1,
  position: 'relative' as const,
  overflow: 'hidden' as const,
} as const;

export const Editor = memo(
  ({ initialSource, onChange, fileName = 'main.typ' }: EditorProps) => {
    // Internal state management - Editor is uncontrolled
    const {
      textareaRef,
      source,
      setSource,
      activeLineIndex,
      highlightedHtml,
      lineCount,
      handleCursorChange,
      getState,
    } = useEditorState({ initialSource, onChange });

    // Scroll synchronization
    const { highlightRef, lineNumbersRef } = useEditorScroll({ textareaRef });

    // Keyboard shortcuts
    const { handleKeyDown } = useEditorKeyboard({
      source,
      onChange: setSource,
      textareaRef,
      getState,
    });

    // Memoize line number for StatusBar
    const lineNumber = useMemo(() => activeLineIndex + 1, [activeLineIndex]);

    return (
      <div className="typst-editor" style={EDITOR_CONTAINER_STYLE}>
        <style>{editorStyles}</style>

        <FileTab fileName={fileName} />

        <div style={EDITOR_CONTENT_STYLE}>
          <EditorLineNumbersContainer
            count={lineCount}
            activeLine={activeLineIndex}
            lineNumbersRef={lineNumbersRef}
          />

          <div style={EDITOR_TEXTAREA_CONTAINER_STYLE}>
            <EditorHighlight
              html={highlightedHtml}
              highlightRef={highlightRef}
            />
            <EditorTextarea
              value={source}
              onChange={setSource}
              onSelect={handleCursorChange}
              onKeyDown={handleKeyDown}
              textareaRef={textareaRef}
            />
          </div>
        </div>

        <StatusBar lineNumber={lineNumber} />
      </div>
    );
  },
  // Custom comparison - Editor never needs to re-render from parent
  // because it manages its own internal state
  (prevProps, nextProps) => {
    return (
      prevProps.fileName === nextProps.fileName &&
      prevProps.onChange === nextProps.onChange
    );
  }
);

Editor.displayName = 'Editor';
