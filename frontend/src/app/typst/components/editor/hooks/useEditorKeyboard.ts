import { useCallback, useMemo, useRef } from 'react';
import {
  deleteLine,
  duplicateLine,
  indentLines,
  insertLineAbove,
  insertLineBelow,
  moveLineDown,
  moveLineUp,
  outdentLines,
  toggleComment,
} from '../lib';
import type { EditorState } from '../types';
import { isMac } from '../utils';

interface UseEditorKeyboardProps {
  source: string;
  onChange: (source: string) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  getState: () => EditorState;
}

export const useEditorKeyboard = ({
  source,
  onChange,
  textareaRef,
  getState,
}: UseEditorKeyboardProps) => {
  // Use refs to avoid recreating handleKeyDown on every source change
  const sourceRef = useRef(source);
  const onChangeRef = useRef(onChange);
  const getStateRef = useRef(getState);

  // Keep refs in sync
  sourceRef.current = source;
  onChangeRef.current = onChange;
  getStateRef.current = getState;

  // Memoize platform check
  const platformIsMac = useMemo(() => isMac(), []);

  // Apply editor action and update cursor position
  const applyAction = useCallback(
    (action: {
      source: string;
      selectionStart: number;
      selectionEnd: number;
    }) => {
      onChangeRef.current(action.source);
      requestAnimationFrame(() => {
        const textarea = textareaRef.current;
        if (textarea) {
          textarea.selectionStart = action.selectionStart;
          textarea.selectionEnd = action.selectionEnd;
        }
      });
    },
    [textareaRef]
  );

  // Keyboard shortcuts handler - stable reference
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      const mod = platformIsMac ? e.metaKey : e.ctrlKey;
      const shift = e.shiftKey;
      const alt = e.altKey;

      // Tab - Indent
      if (e.key === 'Tab' && !mod && !alt) {
        e.preventDefault();
        const state = getStateRef.current();
        const hasSelection = state.selectionStart !== state.selectionEnd;

        if (shift) {
          // Shift+Tab - Outdent
          applyAction(outdentLines(state));
        } else if (hasSelection) {
          // Tab with selection - Indent lines
          applyAction(indentLines(state));
        } else {
          // Tab without selection - Insert spaces
          const start = textarea.selectionStart;
          const currentSource = sourceRef.current;
          const newSource = `${currentSource.substring(0, start)}  ${currentSource.substring(start)}`;
          onChangeRef.current(newSource);
          requestAnimationFrame(() => {
            textarea.selectionStart = textarea.selectionEnd = start + 2;
          });
        }
        return;
      }

      // Ctrl/Cmd + / - Toggle comment
      if (mod && e.key === '/') {
        e.preventDefault();
        applyAction(toggleComment(getStateRef.current()));
        return;
      }

      // Ctrl/Cmd + ] - Indent
      if (mod && e.key === ']') {
        e.preventDefault();
        applyAction(indentLines(getStateRef.current()));
        return;
      }

      // Ctrl/Cmd + [ - Outdent
      if (mod && e.key === '[') {
        e.preventDefault();
        applyAction(outdentLines(getStateRef.current()));
        return;
      }

      // Ctrl/Cmd + Shift + K - Delete line
      if (mod && shift && e.key === 'K') {
        e.preventDefault();
        applyAction(deleteLine(getStateRef.current()));
        return;
      }

      // Ctrl/Cmd + Shift + D - Duplicate line
      if (mod && shift && e.key === 'D') {
        e.preventDefault();
        applyAction(duplicateLine(getStateRef.current()));
        return;
      }

      // Alt + ArrowUp - Move line up
      if (alt && !mod && !shift && e.key === 'ArrowUp') {
        e.preventDefault();
        applyAction(moveLineUp(getStateRef.current()));
        return;
      }

      // Alt + ArrowDown - Move line down
      if (alt && !mod && !shift && e.key === 'ArrowDown') {
        e.preventDefault();
        applyAction(moveLineDown(getStateRef.current()));
        return;
      }

      // Ctrl/Cmd + Enter - Insert line below
      if (mod && !shift && e.key === 'Enter') {
        e.preventDefault();
        applyAction(insertLineBelow(getStateRef.current()));
        return;
      }

      // Ctrl/Cmd + Shift + Enter - Insert line above
      if (mod && shift && e.key === 'Enter') {
        e.preventDefault();
        applyAction(insertLineAbove(getStateRef.current()));
        return;
      }

      // Home - Smart home (toggle between line start and first non-whitespace)
      if (e.key === 'Home' && !mod && !shift && !alt) {
        e.preventDefault();
        const state = getStateRef.current();
        const currentSource = sourceRef.current;
        const lineStart =
          currentSource.lastIndexOf('\n', state.selectionStart - 1) + 1;
        const lineEnd = currentSource.indexOf('\n', state.selectionStart);
        const lineContent = currentSource.slice(
          lineStart,
          lineEnd === -1 ? undefined : lineEnd
        );
        const firstNonWhitespace = lineContent.search(/\S/);
        const smartPos =
          firstNonWhitespace === -1
            ? lineStart
            : lineStart + firstNonWhitespace;
        const newPos = state.selectionStart === smartPos ? lineStart : smartPos;
        textarea.selectionStart = textarea.selectionEnd = newPos;
        return;
      }

      // End - Go to line end
      if (e.key === 'End' && !mod && !shift && !alt) {
        e.preventDefault();
        const pos = textarea.selectionStart;
        const currentSource = sourceRef.current;
        let lineEnd = currentSource.indexOf('\n', pos);
        if (lineEnd === -1) lineEnd = currentSource.length;
        textarea.selectionStart = textarea.selectionEnd = lineEnd;
        return;
      }
    },
    [applyAction, textareaRef, platformIsMac]
  );

  return {
    handleKeyDown,
  };
};
