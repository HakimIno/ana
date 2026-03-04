import { TypstDocument } from '@myriaddreamin/typst.react';
import { RENDERER_WASM_PATH } from '../constants';
import { RENDERING_CONFIG } from './compiler-config';

/**
 * Configure renderer WASM once at module load
 * This should be called before using TypstDocument
 */
export const configureRenderer = () => {
  TypstDocument.setWasmModuleInitOptions({
    beforeBuild: [
      // Configure pixel-per-pt ratio for high-quality rendering
      // This is applied during renderer initialization
      // biome-ignore lint/suspicious/noExplicitAny: Typst library types are incomplete
      async (module: any) => {
        if (module && typeof module.set_pixel_per_pt === 'function') {
          module.set_pixel_per_pt(RENDERING_CONFIG.pixelPerPt);
        }
      },
    ],
    getModule: () => RENDERER_WASM_PATH,
  });
};

/**
 * Renderer options for document rendering
 */
export const RENDERER_OPTIONS = {
  pixelPerPt: RENDERING_CONFIG.pixelPerPt,
  backgroundColor: RENDERING_CONFIG.backgroundColor,
  format: RENDERING_CONFIG.format,
} as const;
