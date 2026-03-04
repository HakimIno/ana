import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

interface ResizableSplitProps {
  left: React.ReactNode;
  right: React.ReactNode;
  initialLeftWidth?: number; // percent
  minLeftWidth?: number; // percent
  maxLeftWidth?: number; // percent
  style?: React.CSSProperties;
  className?: string;
}

export const ResizableSplit: React.FC<ResizableSplitProps> = ({
  left,
  right,
  initialLeftWidth = 50,
  minLeftWidth = 20,
  maxLeftWidth = 80,
  style,
  className,
}) => {
  const [leftWidth, setLeftWidth] = useState(initialLeftWidth);
  const [isDragging, setIsDragging] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number | null>(null);
  const lastClientXRef = useRef<number>(0);

  const resize = useCallback(
    (e: MouseEvent) => {
      if (!containerRef.current) return;

      // Cancel previous animation frame if exists
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }

      // Store clientX for use in RAF callback
      lastClientXRef.current = e.clientX;

      // Use requestAnimationFrame for smooth updates
      rafRef.current = requestAnimationFrame(() => {
        if (!containerRef.current) return;

        const containerRect = containerRef.current.getBoundingClientRect();
        const newLeftWidth =
          ((lastClientXRef.current - containerRect.left) /
            containerRect.width) *
          100;

        if (newLeftWidth >= minLeftWidth && newLeftWidth <= maxLeftWidth) {
          setLeftWidth(newLeftWidth);
        }

        rafRef.current = null;
      });
    },
    [minLeftWidth, maxLeftWidth]
  );

  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const stopResize = useCallback(() => {
    setIsDragging(false);
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (isDragging) {
      const handleMouseMove = (e: MouseEvent) => {
        e.preventDefault();
        resize(e);
      };

      const handleMouseUp = (e: MouseEvent) => {
        e.preventDefault();
        stopResize();
      };

      // Use passive: false for better performance
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);

      // Prevent text selection and set cursor
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
      document.body.style.pointerEvents = 'none';

      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
        document.body.style.pointerEvents = '';
      };
    }
  }, [isDragging, resize, stopResize]);

  // Memoize styles to prevent unnecessary recalculations
  const leftPanelStyle = useMemo(
    () => ({
      width: `${leftWidth}%`,
      height: '100%',
      overflow: 'hidden',
      willChange: isDragging ? 'width' : 'auto',
    }),
    [leftWidth, isDragging]
  );

  const rightPanelStyle = useMemo(
    () => ({
      flex: 1,
      height: '100%',
      overflow: 'hidden',
      willChange: isDragging ? 'width' : 'auto',
    }),
    [isDragging]
  );

  const resizerStyle = useMemo(
    () => ({
      width: '10px',
      height: '100%',
      cursor: 'col-resize',
      flexShrink: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative' as const,
      zIndex: 10,
      touchAction: 'none',
    }),
    []
  );

  const handleStyle = useMemo(
    () => ({
      width: '4px',
      height: '48px',
      backgroundColor: isHovered || isDragging ? '#FFFFFF' : '#FFFFFF',
      borderRadius: '4px',
      transition: isDragging ? 'none' : 'all 0.15s ease',
      boxShadow:
        isHovered || isDragging
          ? '0 2px 8px rgba(0, 0, 0, 0.15)'
          : '0 1px 3px rgba(0, 0, 0, 0.1)',
      willChange: 'background-color, box-shadow',
    }),
    [isHovered, isDragging]
  );

  const containerStyle = useMemo(
    () => ({
      display: 'flex',
      width: '100%',
      height: '100%',
      overflow: 'hidden',
      ...style,
    }),
    [style]
  );

  return (
    <div ref={containerRef} className={className} style={containerStyle}>
      {/* Left Panel */}
      <div style={leftPanelStyle}>{left}</div>

      {/* Resizer Handle */}
      <div
        role="button"
        aria-label="Resize panels"
        tabIndex={0}
        onMouseDown={startResize}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={resizerStyle}
      >
        {/* Invisible hit area */}
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            backgroundColor: 'transparent',
          }}
        />

        {/* Visible handle */}
        <div style={handleStyle} />
      </div>

      {/* Right Panel */}
      <div style={rightPanelStyle}>{right}</div>
    </div>
  );
};
