// Minimal Dark inspired color palette for Typst editor
export const theme = {
  // Background colors
  bg: '#0d0d0d',
  bgHighlight: '#1a1a1a',
  bgSidebar: '#080808',
  border: '#2a2a2a',

  // Text colors
  text: '#bfbdb6',
  lineNumber: '#3e4451',
  lineNumberActive: '#e6e1cf',

  // Syntax colors
  comment: '#5c6370',
  keyword: '#c594c5',
  function: '#e5c07b',
  string: '#98c379',
  number: '#d19a66',
  operator: '#abb2bf',
  heading: '#61afef',
  emphasis: '#d7dae0',
  strong: '#e06c75',
  math: '#e5c07b',
  label: '#56b6c2',
  raw: '#98c379',

  // UI colors
  caret: '#e06c75',
} as const;

export type Theme = typeof theme;
