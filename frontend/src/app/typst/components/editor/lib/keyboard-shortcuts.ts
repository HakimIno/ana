/**
 * VS Code-like keyboard shortcuts for Typst editor
 */

import type { EditorAction, EditorState } from '../types';
import { getLineInfo, getLineNumber, getLineStartByNumber } from '../utils';

/**
 * Toggle line comment (Ctrl/Cmd + /)
 */
export const toggleComment = (state: EditorState): EditorAction => {
  const { source, selectionStart, selectionEnd } = state;
  const startLine = getLineNumber(source, selectionStart);
  const endLine = getLineNumber(source, selectionEnd);
  const lines = source.split('\n');

  // Check if all selected lines are commented
  const selectedLines = lines.slice(startLine, endLine + 1);
  const allCommented = selectedLines.every(line =>
    line.trimStart().startsWith('//')
  );

  // Toggle comments
  const newLines = [...lines];
  for (let i = startLine; i <= endLine; i++) {
    if (allCommented) {
      // Remove comment
      newLines[i] = newLines[i].replace(/^(\s*)\/\/\s?/, '$1');
    } else {
      // Add comment
      newLines[i] = newLines[i].replace(/^(\s*)/, '$1// ');
    }
  }

  const newSource = newLines.join('\n');
  const lengthDiff = newSource.length - source.length;

  return {
    source: newSource,
    selectionStart: selectionStart,
    selectionEnd: selectionEnd + lengthDiff,
  };
};

/**
 * Indent line(s) (Tab or Ctrl/Cmd + ])
 */
export const indentLines = (state: EditorState): EditorAction => {
  const { source, selectionStart, selectionEnd } = state;
  const startLine = getLineNumber(source, selectionStart);
  const endLine = getLineNumber(source, selectionEnd);
  const lines = source.split('\n');

  const newLines = [...lines];
  for (let i = startLine; i <= endLine; i++) {
    newLines[i] = `  ${newLines[i]}`;
  }

  const linesAffected = endLine - startLine + 1;
  return {
    source: newLines.join('\n'),
    selectionStart: selectionStart + 2,
    selectionEnd: selectionEnd + 2 * linesAffected,
  };
};

/**
 * Outdent line(s) (Shift+Tab or Ctrl/Cmd + [)
 */
export const outdentLines = (state: EditorState): EditorAction => {
  const { source, selectionStart, selectionEnd } = state;
  const startLine = getLineNumber(source, selectionStart);
  const endLine = getLineNumber(source, selectionEnd);
  const lines = source.split('\n');

  const newLines = [...lines];
  let startDiff = 0;
  let totalDiff = 0;

  for (let i = startLine; i <= endLine; i++) {
    const match = newLines[i].match(/^( {1,2}|\t)/);
    if (match) {
      const removed = match[0].length;
      newLines[i] = newLines[i].slice(removed);
      totalDiff += removed;
      if (i === startLine) startDiff = removed;
    }
  }

  return {
    source: newLines.join('\n'),
    selectionStart: Math.max(0, selectionStart - startDiff),
    selectionEnd: selectionEnd - totalDiff,
  };
};

/**
 * Delete line (Ctrl/Cmd + Shift + K)
 */
export const deleteLine = (state: EditorState): EditorAction => {
  const { source, selectionStart } = state;
  const { lineStart, lineEnd } = getLineInfo(source, selectionStart);

  // Include the newline character if not the last line
  const deleteEnd = lineEnd < source.length ? lineEnd + 1 : lineEnd;
  const deleteStart =
    lineEnd >= source.length && lineStart > 0 ? lineStart - 1 : lineStart;

  const newSource = source.slice(0, deleteStart) + source.slice(deleteEnd);
  const newPos = Math.min(deleteStart, newSource.length);

  return {
    source: newSource,
    selectionStart: newPos,
    selectionEnd: newPos,
  };
};

/**
 * Duplicate line (Ctrl/Cmd + Shift + D)
 */
export const duplicateLine = (state: EditorState): EditorAction => {
  const { source, selectionStart, selectionEnd } = state;
  const startLine = getLineNumber(source, selectionStart);
  const endLine = getLineNumber(source, selectionEnd);
  const lines = source.split('\n');

  const linesToDuplicate = lines.slice(startLine, endLine + 1);
  const duplicatedContent = linesToDuplicate.join('\n');

  // Insert after the last selected line
  const insertPos = getLineStartByNumber(source, endLine + 1);
  const newSource = `${source.slice(0, insertPos)}${duplicatedContent}\n${source.slice(insertPos)}`;

  const offsetLength = duplicatedContent.length + 1;

  return {
    source: newSource,
    selectionStart: selectionStart + offsetLength,
    selectionEnd: selectionEnd + offsetLength,
  };
};

/**
 * Move line up (Alt + Up)
 */
export const moveLineUp = (state: EditorState): EditorAction => {
  const { source, selectionStart, selectionEnd } = state;
  const startLine = getLineNumber(source, selectionStart);
  const endLine = getLineNumber(source, selectionEnd);

  if (startLine === 0) {
    return state; // Already at top
  }

  const lines = source.split('\n');
  const linesToMove = lines.splice(startLine, endLine - startLine + 1);
  lines.splice(startLine - 1, 0, ...linesToMove);

  const prevLineLength = lines[startLine].length + 1; // +1 for newline

  return {
    source: lines.join('\n'),
    selectionStart: selectionStart - prevLineLength,
    selectionEnd: selectionEnd - prevLineLength,
  };
};

/**
 * Move line down (Alt + Down)
 */
export const moveLineDown = (state: EditorState): EditorAction => {
  const { source, selectionStart, selectionEnd } = state;
  const startLine = getLineNumber(source, selectionStart);
  const endLine = getLineNumber(source, selectionEnd);
  const lines = source.split('\n');

  if (endLine >= lines.length - 1) {
    return state; // Already at bottom
  }

  const linesToMove = lines.splice(startLine, endLine - startLine + 1);
  lines.splice(startLine + 1, 0, ...linesToMove);

  const nextLineLength = lines[startLine].length + 1; // +1 for newline

  return {
    source: lines.join('\n'),
    selectionStart: selectionStart + nextLineLength,
    selectionEnd: selectionEnd + nextLineLength,
  };
};

/**
 * Insert line below (Ctrl/Cmd + Enter)
 */
export const insertLineBelow = (state: EditorState): EditorAction => {
  const { source, selectionStart } = state;
  const { lineEnd } = getLineInfo(source, selectionStart);

  const newSource = `${source.slice(0, lineEnd)}\n${source.slice(lineEnd)}`;
  const newPos = lineEnd + 1;

  return {
    source: newSource,
    selectionStart: newPos,
    selectionEnd: newPos,
  };
};

/**
 * Insert line above (Ctrl/Cmd + Shift + Enter)
 */
export const insertLineAbove = (state: EditorState): EditorAction => {
  const { source, selectionStart } = state;
  const { lineStart } = getLineInfo(source, selectionStart);

  const newSource = `${source.slice(0, lineStart)}\n${source.slice(lineStart)}`;

  return {
    source: newSource,
    selectionStart: lineStart,
    selectionEnd: lineStart,
  };
};
