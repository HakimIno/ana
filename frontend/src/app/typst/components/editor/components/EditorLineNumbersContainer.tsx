'use client';

import { memo } from 'react';
import { editorFontStyles } from '../styles';
import { theme } from '../theme';
import { LineNumbers } from './LineNumbers';

interface EditorLineNumbersContainerProps {
  count: number;
  activeLine: number;
  lineNumbersRef: React.RefObject<HTMLDivElement | null>;
}

export const EditorLineNumbersContainer = memo(
  ({ count, activeLine, lineNumbersRef }: EditorLineNumbersContainerProps) => {
    return (
      <div
        ref={lineNumbersRef}
        style={{
          minWidth: '50px',
          backgroundColor: theme.bgSidebar,
          ...editorFontStyles,
          padding: '12px 0',
          textAlign: 'right',
          borderRight: `1px solid ${theme.border}`,
          overflow: 'hidden',
          userSelect: 'none',
        }}
      >
        <LineNumbers count={count} activeLine={activeLine} />
      </div>
    );
  }
);

EditorLineNumbersContainer.displayName = 'EditorLineNumbersContainer';
