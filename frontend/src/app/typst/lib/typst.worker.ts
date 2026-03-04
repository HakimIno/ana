import type {
  ProxyContext,
  TypstCompiler as TypstCompilerRaw,
} from '@myriaddreamin/typst-ts-web-compiler';
import { COMPILER_WASM_PATH } from '../constants';
import { getAllFontUrls } from '../lib/compiler-config';

// ---- Constants & Interfaces ----

const TYPST_PACKAGE_PROXY = '/api/typst-packages';

interface PackageSpec {
  namespace: string;
  name: string;
  version: string;
}

// Internal state
let compiler: TypstCompilerRaw | null = null;
let proxyContext: ProxyContext | null = null;

// Caches
const packagePathCache = new Map<string, string>();
const virtualFileSystem = new Map<
  string,
  { data: Uint8Array; mtime: number }
>();
const sourceFiles = new Map<string, string>();

// ---- Helper Functions ----

const normalizePath = (path: string): string => {
  return path.replace(/^\/+|\/+$/g, '').replace(/\/+/g, '/');
};

const getPathVariations = (path: string): string[] => {
  const normalized = normalizePath(path);
  const variations = new Set<string>();
  variations.add(normalized);
  variations.add(`/${normalized}`);
  if (path !== normalized && path !== `/${normalized}`) {
    variations.add(path);
  }
  if (normalized.startsWith('@packages/')) {
    variations.add(normalized.substring(1));
    variations.add(`/${normalized.substring(1)}`);
  }
  return Array.from(variations);
};

const fetchFont = async (url: string): Promise<Uint8Array> => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to fetch font: ${url}`);
  const buffer = await response.arrayBuffer();
  return new Uint8Array(buffer);
};

const fetchPackageSync = (spec: PackageSpec): Uint8Array | undefined => {
  const url = new URL(
    `${TYPST_PACKAGE_PROXY}/${spec.name}-${spec.version}.tar.gz`,
    self.location.origin
  ).href;
  try {
    const request = new XMLHttpRequest();
    request.overrideMimeType('text/plain; charset=x-user-defined');
    request.open('GET', url, false); // Synchronous
    request.send(null);

    if (request.status === 200 && typeof request.response === 'string') {
      return Uint8Array.from(request.response, (c: string) => c.charCodeAt(0));
    }
  } catch (e) {
    // biome-ignore lint/suspicious/noConsole: Debugging
    console.warn(`[Typst Worker] Failed to fetch package ${spec.name}:`, e);
  }
  return undefined;
};

const resolvePackage = (spec: PackageSpec): string | undefined => {
  if (spec.namespace !== 'preview') return undefined;

  const cacheKey = `${spec.namespace}/${spec.name}/${spec.version}`;
  if (packagePathCache.has(cacheKey)) {
    return packagePathCache.get(cacheKey);
  }

  const data = fetchPackageSync(spec);
  if (!data) return undefined;

  const packageDir = `@packages/${spec.namespace}/${spec.name}/${spec.version}`;

  try {
    if (!proxyContext) throw new Error('ProxyContext not initialized');

    proxyContext.untar(
      data,
      (path: string, fileData: Uint8Array, mtime: number) => {
        const normalizedTarPath = path.replace(/^\.\//, '');
        const packageRelativePath = `${packageDir}/${normalizedTarPath}`;
        const variations = getPathVariations(packageRelativePath);
        for (const variant of variations) {
          virtualFileSystem.set(variant, { data: fileData, mtime });
        }
      }
    );

    packagePathCache.set(cacheKey, packageDir);
    return packageDir;
  } catch (err) {
    // biome-ignore lint/suspicious/noConsole: Debugging
    console.error(`[Typst Worker] Failed to resolve package ${cacheKey}:`, err);
    return undefined;
  }
};

// ---- Core Logic ----

const findFile = (
  path: string
): { data: Uint8Array; mtime: number } | { content: string } | null => {
  const normalized = normalizePath(path);
  if (sourceFiles.has(normalized)) {
    const content = sourceFiles.get(normalized);
    // biome-ignore lint/style/noNonNullAssertion: Checked with has()
    return { content: content! };
  }

  const variations = getPathVariations(path);
  for (const variant of variations) {
    const file = virtualFileSystem.get(variant);
    if (file) return file;
  }
  return null;
};

async function initCompiler() {
  if (compiler) return;

  const compilerModule = await import('@myriaddreamin/typst-ts-web-compiler');
  // Resolve WASM path to full URL to avoid issues with relative paths in worker
  const wasmUrl = new URL(COMPILER_WASM_PATH, self.location.origin).href;
  await compilerModule.default(wasmUrl);

  const builder = new compilerModule.TypstCompilerBuilder();

  await builder.set_access_model(
    {},
    // mtime
    (path: string) => {
      const file = findFile(path);
      if (!file) return undefined;
      return 'content' in file ? Date.now() : file.mtime;
    },
    // is_file
    (path: string) => findFile(path) !== null,
    // real_path
    (path: string) => {
      const file = findFile(path);
      return file ? normalizePath(path) : undefined;
    },
    // read_all
    (path: string) => {
      const file = findFile(path);
      if (!file) return undefined;
      return 'content' in file
        ? new TextEncoder().encode(file.content)
        : file.data;
    }
  );

  proxyContext = new compilerModule.ProxyContext({});
  const packageResolutionCache = new Map<string, string | undefined>();

  await builder.set_package_registry(proxyContext, (spec: PackageSpec) => {
    const cacheKey = `${spec.namespace}/${spec.name}/${spec.version}`;
    if (packageResolutionCache.has(cacheKey)) {
      return packageResolutionCache.get(cacheKey);
    }
    const result = resolvePackage(spec);
    packageResolutionCache.set(cacheKey, result);
    return result;
  });

  // Load fonts with proper error handling
  try {
    const fontUrls = getAllFontUrls().map(
      f => new URL(f, self.location.origin).href
    );

    // biome-ignore lint/suspicious/noConsole: Debugging
    console.log(`[Typst Worker] Loading ${fontUrls.length} fonts...`);

    // Load fonts in parallel with individual error handling
    const fontPromises = fontUrls.map(async url => {
      try {
        const font = await fetchFont(url);
        return { url, font, success: true };
      } catch (err) {
        // biome-ignore lint/suspicious/noConsole: Debugging
        console.warn(`[Typst Worker] Failed to load font ${url}:`, err);
        return { url, font: null, success: false };
      }
    });

    const fontResults = await Promise.all(fontPromises);

    // Add successfully loaded fonts
    let loadedCount = 0;
    for (const result of fontResults) {
      if (result.success && result.font) {
        await builder.add_raw_font(result.font);
        loadedCount++;
      }
    }

    // biome-ignore lint/suspicious/noConsole: Debugging
    console.log(
      `[Typst Worker] Successfully loaded ${loadedCount}/${fontUrls.length} fonts`
    );

    if (loadedCount === 0) {
      throw new Error('No fonts could be loaded');
    }
  } catch (err) {
    // biome-ignore lint/suspicious/noConsole: Error logging
    console.error('[Typst Worker] Critical font loading error:', err);
    throw err;
  }

  compiler = await builder.build();
}

// ---- Message Handling ----

self.onmessage = async (e: MessageEvent) => {
  const { type, payload, id } = e.data;

  try {
    // biome-ignore lint/suspicious/noImplicitAnyLet: Complex result type
    let result;

    switch (type) {
      case 'INIT':
        await initCompiler();
        result = { success: true };
        break;

      case 'RESET':
        if (!compiler) throw new Error('Compiler not initialized');
        compiler.reset();
        sourceFiles.clear();
        result = { success: true };
        break;

      case 'ADD_SOURCE': {
        if (!compiler) throw new Error('Compiler not initialized');
        const { path, content } = payload;
        const normalized = normalizePath(path);
        sourceFiles.set(normalized, content);
        compiler.add_source(path, content);
        result = { success: true };
        break;
      }

      case 'COMPILE': {
        if (!compiler) throw new Error('Compiler not initialized');
        const { mainFilePath } = payload;
        const compilationResult = compiler.compile(
          mainFilePath,
          null,
          'vector', // Switch to SVG to fix layout artifacts
          3 // Full diagnostics
        );

        // Log for debugging
        // biome-ignore lint/suspicious/noConsole: Debugging
        console.log(
          '[Typst Worker] Compilation result keys:',
          Object.keys(compilationResult || {})
        );
        // biome-ignore lint/suspicious/noConsole: Debugging
        console.log(
          '[Typst Worker] Result type:',
          typeof compilationResult?.result
        );

        // Extract and ensure proper serialization of the result
        // The raw compiler might return the artifact directly or in a nested property
        let artifactData: Uint8Array | undefined;
        let diagnosticsData: unknown[] = [];

        if (compilationResult) {
          // Check various possible structures
          if (compilationResult.result instanceof Uint8Array) {
            artifactData = compilationResult.result;
          } else if (compilationResult instanceof Uint8Array) {
            // Result is directly the artifact
            artifactData = compilationResult;
          } else if (
            typeof compilationResult.result === 'object' &&
            compilationResult.result !== null
          ) {
            // Might be ArrayBuffer or similar
            if (compilationResult.result.buffer) {
              artifactData = new Uint8Array(compilationResult.result.buffer);
            }
          }

          if (compilationResult.diagnostics) {
            diagnosticsData = compilationResult.diagnostics;
          }
        }

        // biome-ignore lint/suspicious/noConsole: Debugging
        console.log(
          '[Typst Worker] Artifact extracted:',
          artifactData ? `${artifactData.length} bytes` : 'none'
        );
        // biome-ignore lint/suspicious/noConsole: Debugging
        console.log('[Typst Worker] Diagnostics:', diagnosticsData.length);

        // Return properly formatted result
        result = {
          result: artifactData,
          diagnostics: diagnosticsData,
        };
        break;
      }

      case 'EXPORT_PDF': {
        if (!compiler) throw new Error('Compiler not initialized');
        const { mainFilePath } = payload;
        const compilationResult = compiler.compile(
          mainFilePath,
          null,
          'pdf', // PDF format
          3 // Full diagnostics
        );

        let artifactData: Uint8Array | undefined;

        if (compilationResult) {
          // Check various possible structures for PDF output
          if (compilationResult.result instanceof Uint8Array) {
            artifactData = compilationResult.result;
          } else if (compilationResult instanceof Uint8Array) {
            artifactData = compilationResult;
          } else if (
            typeof compilationResult.result === 'object' &&
            compilationResult.result !== null
          ) {
            if (compilationResult.result.buffer) {
              artifactData = new Uint8Array(compilationResult.result.buffer);
            }
          }
        }

        result = {
          result: artifactData,
        };
        break;
      }

      case 'EXPORT_SVG': {
        if (!compiler) throw new Error('Compiler not initialized');
        const { mainFilePath } = payload;
        const compilationResult = compiler.compile(
          mainFilePath,
          null,
          'vector', // SVG format
          3 // Full diagnostics
        );

        let artifactData: Uint8Array | undefined;

        if (compilationResult) {
          if (compilationResult.result instanceof Uint8Array) {
            artifactData = compilationResult.result;
          } else if (compilationResult instanceof Uint8Array) {
            artifactData = compilationResult;
          } else if (
            typeof compilationResult.result === 'object' &&
            compilationResult.result !== null
          ) {
            if (compilationResult.result.buffer) {
              artifactData = new Uint8Array(compilationResult.result.buffer);
            }
          }
        }

        result = {
          result: artifactData,
        };
        break;
      }

      default:
        throw new Error(`Unknown message type: ${type}`);
    }

    self.postMessage({ type: `${type}_RESULT`, id, payload: result });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    self.postMessage({ type: 'ERROR', id, error: errorMessage });
  }
};
