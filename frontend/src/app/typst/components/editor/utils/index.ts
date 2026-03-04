// Editor utility functions

/**
 * Get line number from cursor position
 */
export const getLineNumber = (source: string, position: number): number => {
  return source.slice(0, position).split('\n').length - 1;
};

/**
 * Get line boundaries from position
 */
export const getLineInfo = (source: string, position: number) => {
  const lineStart = source.lastIndexOf('\n', position - 1) + 1;
  const lineEnd = source.indexOf('\n', position);
  return {
    lineStart,
    lineEnd: lineEnd === -1 ? source.length : lineEnd,
    lineContent: source.slice(lineStart, lineEnd === -1 ? undefined : lineEnd),
  };
};

/**
 * Get line start position by line number
 */
export const getLineStartByNumber = (
  source: string,
  lineNum: number
): number => {
  const lines = source.split('\n');
  let pos = 0;
  for (let i = 0; i < lineNum && i < lines.length; i++) {
    pos += lines[i].length + 1;
  }
  return pos;
};

/**
 * Check if platform is Mac
 */
export const isMac = (): boolean => {
  return (
    typeof navigator !== 'undefined' &&
    navigator.platform.toUpperCase().indexOf('MAC') >= 0
  );
};
