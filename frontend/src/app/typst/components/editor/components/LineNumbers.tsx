'use client';

import { memo, useMemo } from 'react';

interface LineNumbersProps {
  count: number;
  activeLine: number;
}

// Individual line number component - only re-renders when its active state changes
const LineNumber = memo(
  ({ lineNum, isActive }: { lineNum: number; isActive: boolean }) => (
    <div className={isActive ? 'ln-active' : 'ln'}>{lineNum}</div>
  ),
  (prevProps, nextProps) =>
    prevProps.lineNum === nextProps.lineNum &&
    prevProps.isActive === nextProps.isActive
);

LineNumber.displayName = 'LineNumber';

export const LineNumbers = memo(
  ({ count, activeLine }: LineNumbersProps) => {
    // Only regenerate array when count changes
    const lineNumbers = useMemo(() => {
      return Array.from({ length: count }, (_, i) => i);
    }, [count]);

    return (
      <>
        {lineNumbers.map(i => (
          <LineNumber key={i} lineNum={i + 1} isActive={i === activeLine} />
        ))}
      </>
    );
  },
  // Re-render when count or activeLine changes
  (prevProps, nextProps) =>
    prevProps.count === nextProps.count &&
    prevProps.activeLine === nextProps.activeLine
);

LineNumbers.displayName = 'LineNumbers';
