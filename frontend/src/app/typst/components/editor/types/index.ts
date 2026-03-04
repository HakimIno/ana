// Editor component types
export interface EditorProps {
  /** Initial source code (uncontrolled) */
  initialSource: string;
  /** Callback when source changes - for external compilation */
  onChange: (source: string) => void;
  fileName?: string;
}

// Editor state types
export interface EditorState {
  source: string;
  selectionStart: number;
  selectionEnd: number;
}

export interface EditorAction {
  source: string;
  selectionStart: number;
  selectionEnd: number;
}
