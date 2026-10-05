import { cpp } from '@codemirror/lang-cpp'
import { go } from '@codemirror/lang-go'
import { java } from '@codemirror/lang-java'
import { javascript } from '@codemirror/lang-javascript'
import { php } from '@codemirror/lang-php'
import { python } from '@codemirror/lang-python'
import { rust } from '@codemirror/lang-rust'
import { StreamLanguage } from '@codemirror/language'
import type { Extension } from '@codemirror/state'
import { csharp } from '@codemirror/legacy-modes/mode/clike'
import { haskell } from '@codemirror/legacy-modes/mode/haskell'
import { fSharp } from '@codemirror/legacy-modes/mode/mllike'
import { ruby } from '@codemirror/legacy-modes/mode/ruby'
import CodeMirror, { EditorView } from '@uiw/react-codemirror'
import type { CodeEditorProps } from './code-editor'

/** Syntax by the family in a compiler id such as `python-3.14` or `dotnet-csharp-9`. */
const SYNTAX: [RegExp, () => Extension][] = [
  [/^python/, python],
  [/^typescript/, () => javascript({ typescript: true })],
  [/^openjdk/, java],
  [/^(g\+\+|gcc)/, cpp],
  [/^go/, go],
  [/^rust/, rust],
  [/^php/, () => php({ plain: true })],
  [/csharp/, () => StreamLanguage.define(csharp)],
  [/fsharp/, () => StreamLanguage.define(fSharp)],
  [/^ruby/, () => StreamLanguage.define(ruby)],
  [/^haskell/, () => StreamLanguage.define(haskell)],
]

export default function CodeMirrorEditor({
  value,
  language,
  label,
  readOnly,
  height = '360px',
  onChange,
  onPaste,
}: CodeEditorProps) {
  const syntax = SYNTAX.find(([pattern]) => pattern.test(language))?.[1]
  const extensions = [
    EditorView.contentAttributes.of({ 'aria-label': label }),
    EditorView.domEventHandlers({ paste: () => onPaste?.() }),
    ...(syntax ? [syntax()] : []),
  ]

  return (
    <CodeMirror
      value={value}
      height={height}
      theme="dark"
      readOnly={readOnly}
      extensions={extensions}
      onChange={onChange}
    />
  )
}
