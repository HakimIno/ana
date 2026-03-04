// Typst syntax highlighter - fast regex-based line highlighting

const escapeHtml = (text: string): string => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
};

/**
 * Highlight a single line of Typst code
 * Returns HTML string with syntax highlighting spans
 */
export const highlightLine = (line: string): string => {
  let html = escapeHtml(line);

  // Early return for empty lines
  if (!html) return html;

  // Full line comment
  if (html.trimStart().startsWith('//')) {
    return `<span class="hl-comment">${html}</span>`;
  }

  // Heading (= at start of line)
  if (/^=+\s/.test(html)) {
    return `<span class="hl-heading">${html}</span>`;
  }

  // Apply token highlights using regex
  html = html
    // Strings "..."
    .replace(/"[^"]*"/g, '<span class="hl-string">$&</span>')
    // Math $...$
    .replace(/\$[^$]+\$/g, '<span class="hl-math">$&</span>')
    // Keywords #let, #set, etc.
    .replace(
      /#(let|set|show|import|include|if|else|for|while|return|break|continue|none|auto|true|false)\b/g,
      '<span class="hl-keyword">$&</span>'
    )
    // Functions #name
    .replace(/#[a-zA-Z_][a-zA-Z0-9_]*/g, '<span class="hl-function">$&</span>')
    // Labels <name>
    .replace(
      /&lt;[a-zA-Z_][a-zA-Z0-9_-]*&gt;/g,
      '<span class="hl-label">$&</span>'
    )
    // References @name
    .replace(/@[a-zA-Z_][a-zA-Z0-9_-]*/g, '<span class="hl-label">$&</span>')
    // Numbers with optional units
    .replace(
      /\b\d+\.?\d*(?:pt|em|cm|mm|in|%|fr)?\b/g,
      '<span class="hl-number">$&</span>'
    );

  return html;
};

/**
 * Highlight entire source code
 * Processes line by line for better performance
 */
export const highlightSource = (source: string): string => {
  return source.split('\n').map(highlightLine).join('\n');
};
