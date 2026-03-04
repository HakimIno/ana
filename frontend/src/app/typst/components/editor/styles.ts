import { theme } from './theme';

// Editor CSS styles - injected once via <style> tag
export const editorStyles = `
.typst-editor .hl-comment { color: ${theme.comment}; font-style: italic; }
.typst-editor .hl-heading { color: ${theme.heading}; font-weight: 600; }
.typst-editor .hl-string { color: ${theme.string}; }
.typst-editor .hl-math { color: ${theme.math}; }
.typst-editor .hl-keyword { color: ${theme.keyword}; }
.typst-editor .hl-function { color: ${theme.function}; }
.typst-editor .hl-label { color: ${theme.label}; }
.typst-editor .hl-number { color: ${theme.number}; }
.typst-editor .ln { color: ${theme.lineNumber}; padding-right: 8px; }
.typst-editor .ln-active { color: ${theme.lineNumberActive}; font-weight: 600; padding-right: 8px; }
`;

// Shared editor font styles
export const editorFontStyles = {
  fontFamily: '"JetBrains Mono", "Fira Code", Consolas, monospace',
  fontSize: '14px',
  lineHeight: 1.5,
} as const;
