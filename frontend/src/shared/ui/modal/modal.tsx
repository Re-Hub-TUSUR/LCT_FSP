import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import './modal.css'

type Props = {
  title: string
  onClose: () => void
  children: ReactNode
}

/** Modal dialog on the native `<dialog>`: the focus trap and Esc come from the browser. */
export function Modal({ title, onClose, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = ref.current
    if (!dialog || dialog.open) return
    // Environments without the modal API (old browsers, jsdom) still get an open dialog.
    if (typeof dialog.showModal === 'function') dialog.showModal()
    else dialog.setAttribute('open', '')
  }, [])

  return (
    <dialog ref={ref} className="modal" aria-labelledby={titleId} onClose={onClose}>
      <div className="modal__panel">
        <header className="modal__head">
          <h2 id={titleId} className="modal__title">
            {title}
          </h2>
          <button type="button" className="modal__close" aria-label="Закрыть" onClick={onClose}>
            ×
          </button>
        </header>
        {children}
      </div>
    </dialog>
  )
}
