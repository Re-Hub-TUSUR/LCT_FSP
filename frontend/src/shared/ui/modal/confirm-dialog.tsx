import type { ReactNode } from 'react'
import { Button } from '../button/button'
import { Modal } from './modal'

type Props = {
  title: string
  children?: ReactNode
  confirmLabel: string
  /** True while the confirmed action runs: both buttons wait. */
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

/** «Are you sure?» for actions that cannot be undone. */
export function ConfirmDialog({ title, children, confirmLabel, busy, onConfirm, onCancel }: Props) {
  return (
    <Modal title={title} onClose={onCancel} danger>
      {children && <div className="modal__text">{children}</div>}
      <div className="modal__actions">
        <Button disabled={busy} onClick={onConfirm}>
          {confirmLabel}
        </Button>
        <Button variant="ghost" disabled={busy} onClick={onCancel}>
          Отмена
        </Button>
      </div>
    </Modal>
  )
}
