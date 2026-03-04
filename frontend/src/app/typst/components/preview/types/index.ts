// Preview component types
export interface PreviewProps {
  artifact: Uint8Array | null;
  error: string | null;
  isCompiling: boolean;
  onExportPdf?: () => void;
}
