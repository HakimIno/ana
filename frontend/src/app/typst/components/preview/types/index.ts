// Preview component types
export interface PreviewProps {
  artifact: Uint8Array | null;
  error: string | null;
  isCompiling: boolean;
  onGenerated: (source: string) => void;
  onExportPdf?: () => void;
}
