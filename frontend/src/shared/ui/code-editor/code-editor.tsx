import { Suspense, lazy } from 'react'
import './code-editor.css'

export type CodeEditorProps = {
  value: string
  /** Compiler id (`python-3.14`, `g++-15`, …): picks the syntax highlighting. */
  language: string
  /** Accessible name of the editing area. */
  label: string
  readOnly?: boolean
  height?: string
  onChange: (value: string) => void
  onPaste?: () => void
}

// CodeMirror with its language packs is heavy and needed on two screens only.
const CodeMirrorEditor = lazy(() => import('./code-mirror'))

export function CodeEditor(props: CodeEditorProps) {
  return (
    <div className="code-editor">
      <Suspense
        fallback={
          <p className="code-editor__loading" style={{ height: props.height ?? '360px' }}>
            Загружаем редактор…
          </p>
        }
      >
        <CodeMirrorEditor {...props} />
      </Suspense>
    </div>
  )
}
