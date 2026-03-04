// Typst compiler constants
export const COMPILER_WASM_PATH = '/typst_ts_web_compiler_bg.wasm';
export const RENDERER_WASM_PATH = '/typst_ts_renderer_bg.wasm';
export const DOCUMENT_PATH = '/document.typ';

// UI constants
export const BACKGROUND_COLOR = '#343541';
export const DOCUMENT_FILL = '#ffffff';

// Legacy exports for backward compatibility
export const THAI_FONTS = [
  '/fonts/THSarabunNew/THSarabunNew.ttf',
  '/fonts/THSarabunNew/THSarabunNewBold.ttf',
  '/fonts/THSarabunNew/THSarabunNewItalic.ttf',
  '/fonts/THSarabunNew/THSarabunNewBoldItalic.ttf',
  '/fonts/libertinus/LibertinusSerif-Regular.otf',
  '/fonts/libertinus/LibertinusSerif-Bold.otf',
  '/fonts/libertinus/LibertinusSerif-Italic.otf',
  '/fonts/libertinus/LibertinusSerif-BoldItalic.otf',
] as const;

export const DEFAULT_TYPST_PREAMBLE = `#set text(font: ("TH Sarabun New", "Libertinus Serif"))
#set page(width: 595.28pt, height: 841.89pt, margin: 2.5cm)
`;
