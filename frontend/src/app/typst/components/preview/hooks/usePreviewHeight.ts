import { useEffect } from 'react';

/**
 * Fix Typst document container height when artifact changes
 */
export const usePreviewHeight = (artifact: Uint8Array | null) => {
  useEffect(() => {
    if (!artifact) return;

    // Use setTimeout to ensure DOM is ready
    const timeoutId = setTimeout(() => {
      const typstApp = document.querySelector<HTMLElement>('.typst-app');
      if (typstApp) {
        typstApp.style.height = 'auto';
        typstApp.style.minHeight = '100%';
      }
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [artifact]);
};
