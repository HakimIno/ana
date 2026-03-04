'use client';

import { memo, useCallback, useRef } from 'react';
import { editorFontStyles } from '../styles';
import { theme } from '../theme';

interface EditorTextareaProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: () => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}

// Static style object - created once
const TEXTAREA_STYLE = {
  position: 'absolute' as const,
  inset: 0,
  padding: '12px',
  ...editorFontStyles,
  color: 'transparent',
  caretColor: theme.caret,
  backgroundColor: 'transparent',
  border: 'none',
  outline: 'none',
  resize: 'none' as const,
  whiteSpace: 'pre' as const,
  wordWrap: 'normal' as const,
  overflow: 'auto' as const,
  tabSize: 2,
} as const;

export const EditorTextarea = memo(
  ({
    value,
    onChange,
    onSelect,
    onKeyDown,
    textareaRef,
  }: EditorTextareaProps) => {
    // Use ref to track if we're in the middle of composition (IME input)
    const isComposingRef = useRef(false);

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        // Don't update during IME composition
        if (isComposingRef.current) return;
        onChange(e.target.value);
      },
      [onChange]
    );

    const handleCompositionStart = useCallback(() => {
      isComposingRef.current = true;
    }, []);

    const handleCompositionEnd = useCallback(
      (e: React.CompositionEvent<HTMLTextAreaElement>) => {
        isComposingRef.current = false;
        // Update with final composed value
        onChange((e.target as HTMLTextAreaElement).value);
      },
      [onChange]
    );

    return (
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onSelect={onSelect}
        onKeyDown={onKeyDown}
        onClick={onSelect}
        onCompositionStart={handleCompositionStart}
        onCompositionEnd={handleCompositionEnd}
        style={TEXTAREA_STYLE}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        autoComplete="off"
      />
    );
  },
  // Custom comparison - only re-render when value changes
  (prevProps, nextProps) => {
    return (
      prevProps.value === nextProps.value &&
      prevProps.onChange === nextProps.onChange &&
      prevProps.onSelect === nextProps.onSelect &&
      prevProps.onKeyDown === nextProps.onKeyDown
    );
  }
);

EditorTextarea.displayName = 'EditorTextarea';
