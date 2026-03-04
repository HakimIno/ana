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
/* Force responsive scaling for Typst output */
.typst-doc, .typst-app {
  width: 100% !important;
  height: auto !important;
  min-height: 0 !important; /* Allow shrinking */
  display: flex !important;
  justify-content: center !important;
}

/* Target SVG deeply to override any library styles */
.preview-container svg,
.typst-doc svg,
.typst-app svg {
  width: 100% !important;
  height: auto !important;
  max-width: 100% !important;
  display: block !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* Add subtle shadow to page */
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
