/**
 * Typst Compiler Wrapper (Web Worker Client)
 * Handles communication with the Typst compiler worker
 */

// Interface for compiler responses
export interface CompileResult {
  result?: Uint8Array;
  diagnostics?: unknown[];
}

export interface TypstCompilerWrapper {
  init(): Promise<void>;
  reset(): Promise<void>;
  addSource(path: string, content: string): Promise<void>;
  compile(options: { mainFilePath: string }): Promise<CompileResult>;
  exportPdf(options: { mainFilePath: string }): Promise<CompileResult>;
  exportSvg(options: { mainFilePath: string }): Promise<CompileResult>;
  exportPng(options: { mainFilePath: string }): Promise<CompileResult>;
  terminate(): void;
}

// Map to track pending requests
const pendingRequests = new Map<
  string,
  // biome-ignore lint/suspicious/noExplicitAny: Generic payload handling
  { resolve: (value: any) => void; reject: (reason: any) => void }
>();

let worker: Worker | null = null;
let workerInitPromise: Promise<void> | null = null;

// Unique ID generator for messages
const generateId = () => Math.random().toString(36).substr(2, 9);

/**
 * Get or create the worker instance
 */
const getWorker = (): Worker => {
  if (!worker) {
    // Create new worker
    // Note: This relies on the build tool (Next.js/Webpack) to handle the import
    worker = new Worker(new URL('./typst.worker.ts', import.meta.url));

    // Set up message listener
    worker.onmessage = (event: MessageEvent) => {
      const { type, id, payload, error } = event.data;

      // Debug logging
      // biome-ignore lint/suspicious/noConsole: Debugging
      console.log('[Typst Client] Received message:', {
        type,
        id,
        hasPayload: !!payload,
        error,
      });
      if (type === 'COMPILE_RESULT' && payload) {
        // biome-ignore lint/suspicious/noConsole: Debugging
        console.log('[Typst Client] Compile result:', {
          hasResult: !!payload.result,
          resultType: payload.result
            ? payload.result.constructor?.name
            : 'none',
          resultLength: payload.result?.length || 0,
          diagnosticsCount: payload.diagnostics?.length || 0,
        });
      }

      if (id && pendingRequests.has(id)) {
        const deferred = pendingRequests.get(id);
        if (deferred) {
          const { resolve, reject } = deferred;
          pendingRequests.delete(id);

          if (error) {
            reject(new Error(error));
          } else {
            resolve(payload);
          }
        }
      }
    };

    worker.onerror = error => {
      // biome-ignore lint/suspicious/noConsole: Error logging
      console.error('[Typst Client] Worker error:', error);
    };
  }
  return worker;
};

/**
 * Send message to worker and wait for response
 */
// biome-ignore lint/suspicious/noExplicitAny: Payload can be anything
const sendToWorker = <T>(type: string, payload?: any): Promise<T> => {
  const workerInstance = getWorker();
  const id = generateId();

  return new Promise((resolve, reject) => {
    pendingRequests.set(id, { resolve, reject });
    workerInstance.postMessage({ type, payload, id });
  });
};

/**
 * Initialize compiler
 */
const init = async (): Promise<void> => {
  if (workerInitPromise) return workerInitPromise;

  workerInitPromise = sendToWorker('INIT')
    .then(() => {
      // biome-ignore lint/suspicious/noConsole: Debugging
      console.log('[Typst Client] Compiler initialized');
    })
    .catch(err => {
      workerInitPromise = null; // Allow retry
      throw err;
    });

  return workerInitPromise;
};

// Singleton wrapper
export const getCompiler = async (): Promise<TypstCompilerWrapper> => {
  await init();

  return {
    init,

    reset: async () => {
      await sendToWorker('RESET');
    },

    addSource: async (path: string, content: string) => {
      await sendToWorker('ADD_SOURCE', { path, content });
    },

    compile: async ({ mainFilePath }) => {
      return sendToWorker<CompileResult>('COMPILE', { mainFilePath });
    },

    exportPdf: async ({ mainFilePath }) => {
      return sendToWorker<CompileResult>('EXPORT_PDF', { mainFilePath });
    },

    exportSvg: async ({ mainFilePath }) => {
      return sendToWorker<CompileResult>('EXPORT_SVG', { mainFilePath });
    },

    exportPng: async ({ mainFilePath }) => {
      // PNG export: First get SVG, then convert to PNG using canvas
      const svgResult = await sendToWorker<CompileResult>('EXPORT_SVG', {
        mainFilePath,
      });

      if (!svgResult.result) {
        throw new Error('Failed to generate SVG for PNG conversion');
      }

      // Convert SVG to PNG using canvas
      const svgData = svgResult.result;
      return new Promise<CompileResult>((resolve, reject) => {
        // Create a new ArrayBuffer to ensure compatibility with Blob
        const buffer = new Uint8Array(svgData).buffer;
        const svgBlob = new Blob([buffer], {
          type: 'image/svg+xml',
        });
        const url = URL.createObjectURL(svgBlob);
        const img = new Image();

        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width * 2; // 2x for better quality
          canvas.height = img.height * 2;
          const ctx = canvas.getContext('2d');

          if (!ctx) {
            reject(new Error('Failed to get canvas context'));
            return;
          }

          ctx.scale(2, 2);
          ctx.drawImage(img, 0, 0);
          URL.revokeObjectURL(url);

          canvas.toBlob(blob => {
            if (!blob) {
              reject(new Error('Failed to convert canvas to blob'));
              return;
            }

            blob
              .arrayBuffer()
              .then(buffer => {
                resolve({ result: new Uint8Array(buffer) });
              })
              .catch(reject);
          }, 'image/png');
        };

        img.onerror = () => {
          URL.revokeObjectURL(url);
          reject(new Error('Failed to load SVG image'));
        };

        img.src = url;
      });
    },

    terminate: () => {
      if (worker) {
        worker.terminate();
        worker = null;
        workerInitPromise = null;
        pendingRequests.clear();
      }
    },
  };
};

// Export nothing else, keeping API surface clean
