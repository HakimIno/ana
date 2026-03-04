/**
 * Typst Compiler Configuration
 * Centralized configuration for optimal compilation and rendering
 */

// Page size presets (in points: 1pt = 1/72 inch)
export const PAGE_SIZES = {
  A4: { width: 595.28, height: 841.89 }, // 210mm x 297mm
  LETTER: { width: 612, height: 792 }, // 8.5" x 11"
  LEGAL: { width: 612, height: 1008 }, // 8.5" x 14"
  A5: { width: 420.94, height: 595.28 }, // 148mm x 210mm
  AUTO: { width: 'auto', height: 'auto' }, // For special cases
} as const;

export type PageSizeKey = keyof typeof PAGE_SIZES;

// Default page configuration
export const DEFAULT_PAGE_SIZE: PageSizeKey = 'A4';
export const DEFAULT_PAGE_MARGIN = '2.5cm';

// Rendering configuration
export const RENDERING_CONFIG = {
  // Pixel per point ratio for high-quality rendering
  // 2.0 for retina displays, 1.0 for standard displays
  pixelPerPt: 2.0,

  // Rendering format: 'vector' (SVG) or 'canvas'
  // 'vector' provides better quality, 'canvas' may be faster
  format: 'vector' as const,

  // Background color for the document
  backgroundColor: '#ffffff',

  // Enable incremental compilation
  incremental: true,
} as const;

// Font configuration with proper fallback chains
// TH Sarabun New is listed first to ensure Thai text and numbers render correctly
export const FONT_CONFIG = {
  // Serif fonts (for body text)
  serif: ['TH Sarabun New', 'Libertinus Serif'],

  // Sans-serif fonts
  sans: ['TH Sarabun New'],

  // Monospace fonts (for code)
  mono: ['TH Sarabun New'],

  // Math fonts
  math: ['Libertinus Math', 'New Computer Modern Math'],

  // Thai fonts
  thai: ['TH Sarabun New'],
} as const;

// Font URLs - organized by priority
export const FONT_URLS = {
  // Essential fonts (loaded immediately)
  essential: [
    '/fonts/libertinus/LibertinusSerif-Regular.otf',
    '/fonts/libertinus/LibertinusSerif-Bold.otf',
    '/fonts/libertinus/LibertinusSerif-Italic.otf',
    '/fonts/libertinus/LibertinusSerif-BoldItalic.otf',
    '/fonts/libertinus/LibertinusMath-Regular.otf',
  ],

  // Thai fonts (loaded immediately for Thai support)
  thai: [
    '/fonts/THSarabunNew/THSarabunNew.ttf',
    '/fonts/THSarabunNew/THSarabunNewBold.ttf',
    '/fonts/THSarabunNew/THSarabunNewItalic.ttf',
    '/fonts/THSarabunNew/THSarabunNewBoldItalic.ttf',
  ],

  // Additional fonts (empty - only fonts that exist in public folder)
  additional: [] as string[],
} as const;

// Get all font URLs in loading order
export const getAllFontUrls = (): string[] => {
  return [...FONT_URLS.essential, ...FONT_URLS.thai, ...FONT_URLS.additional];
};

// Compiler performance settings
export const COMPILER_CONFIG = {
  // Debounce delay for compilation (ms)
  debounceMs: 300,

  // Maximum compilation time before warning (ms)
  maxCompilationTime: 5000,

  // Enable compilation caching
  enableCaching: true,

  // Cache size limit (number of cached compilations)
  cacheSize: 10,
} as const;

// Generate Typst preamble with configuration
export const generateTypstPreamble = (
  pageSize: PageSizeKey = DEFAULT_PAGE_SIZE,
  margin: string = DEFAULT_PAGE_MARGIN
): string => {
  const size = PAGE_SIZES[pageSize];

  // For auto sizing, use minimal configuration
  if (pageSize === 'AUTO') {
    return `#set text(font: (${FONT_CONFIG.thai.map(f => `"${f}"`).join(', ')}, ${FONT_CONFIG.serif.map(f => `"${f}"`).join(', ')}))\n#set page(width: auto, height: auto, margin: ${margin})\n`;
  }

  // For standard page sizes, use explicit dimensions
  return `#set text(font: (${FONT_CONFIG.thai.map(f => `"${f}"`).join(', ')}, ${FONT_CONFIG.serif.map(f => `"${f}"`).join(', ')}))\n#set page(width: ${size.width}pt, height: ${size.height}pt, margin: ${margin})\n`;
};

// Export type for page size configuration
export type PageSize = (typeof PAGE_SIZES)[PageSizeKey];
