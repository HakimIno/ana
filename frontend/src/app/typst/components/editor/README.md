# Typst Editor Component

Clean, performant, and well-organized Typst code editor with VS Code-like keyboard shortcuts.

## 📁 Folder Structure

```
editor/
├── Editor.tsx              # Main editor component
├── index.ts                # Public exports
│
├── components/             # UI sub-components
│   ├── EditorTextarea.tsx
│   ├── EditorHighlight.tsx
│   ├── EditorLineNumbersContainer.tsx
│   └── index.ts
│
├── hooks/                  # Custom React hooks
│   ├── useEditorState.ts   # State & highlighting
│   ├── useEditorScroll.ts  # Scroll synchronization
│   ├── useEditorKeyboard.ts # Keyboard shortcuts
│   └── index.ts
│
├── lib/                    # Core logic
│   ├── highlighter.ts      # Syntax highlighting
│   ├── keyboard-shortcuts.ts # VS Code shortcuts
│   └── index.ts
│
├── types/                  # TypeScript types
│   └── index.ts
│
├── utils/                  # Utility functions
│   └── index.ts
│
├── constants/              # Constants
│   └── index.ts
│
├── theme.ts                # Tokyo Night theme
├── styles.ts               # CSS styles
├── FileTab.tsx             # File tab UI
├── LineNumbers.tsx         # Line numbers component
└── StatusBar.tsx           # Status bar
```

## 🚀 Performance Optimizations

- ✅ `memo()` on Editor component
- ✅ `useMemo()` for line count calculation
- ✅ `startTransition()` for syntax highlighting
- ✅ Optimized callbacks with proper dependencies
- ✅ Memoized platform detection

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + /` | Toggle comment |
| `Tab` / `Ctrl/Cmd + ]` | Indent |
| `Shift+Tab` / `Ctrl/Cmd + [` | Outdent |
| `Ctrl/Cmd + Shift + K` | Delete line |
| `Ctrl/Cmd + Shift + D` | Duplicate line |
| `Alt + ↑/↓` | Move line |
| `Ctrl/Cmd + Enter` | Insert line below |
| `Home` | Smart home |
| `End` | Go to line end |

## 📦 Exports

```typescript
export { Editor } from './Editor';
export { theme } from './theme';
export type { Theme } from './theme';
```
