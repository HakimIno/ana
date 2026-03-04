// Preview utility functions

/**
 * Scroll Typst document to fit viewport
 */
export const zoomToFit = () => {
  const typstApp = document.querySelector<HTMLElement>('.typst-app');
  if (typstApp) {
    typstApp.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};
