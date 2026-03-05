// Preview styles
export const previewStyles = `
@keyframes spin {
  to { transform: rotate(360deg); }
}
.typst-app {
  height: auto !important;
  min-height: 100% !important;
  width: 100% !important;
}
/* Force pages to stack vertically */
.typst-doc, .typst-app {
  width: 100% !important;
  height: auto !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  gap: 16px !important;
}

/* Each page: clip overflow so text layers don't bleed out */
.typst-page, .typst-dom-page {
  overflow: hidden !important;
  position: relative !important;
}

/* Each page SVG: full width up to A4-like max, drop shadow */
.preview-container svg,
.typst-doc svg,
.typst-app svg {
  width: 100% !important;
  height: auto !important;
  max-width: 900px !important;
  display: block !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* ── Hide the Typst accessibility/text-selection overlay layers ──────────
   These layers exist for copy-paste and screen readers, but they render
   as visible "ghost text" behind the SVG pages. Hide visually, keep in DOM. */
.typst-html-semantics,
.typst-content-hint,
.typst-content-fallback,
.typst-content-group {
  opacity: 0 !important;
  pointer-events: none !important;
  user-select: none !important;
}

/* Allow text selection to still work on the typst-text spans */
.typst-text {
  color: transparent !important;
  position: absolute !important;
}


`;

export const containerStyles = {
  width: '100%',
  height: '100%',
  display: 'flex',
  flexDirection: 'column' as const,
  backgroundColor: '#ffffff',
  overflow: 'hidden' as const,
  borderRadius: '12px',
};

export const contentStyles = {
  flex: 1,
  overflow: 'auto' as const,
  backgroundColor: '#ffffff',
  padding: '20px',
};
