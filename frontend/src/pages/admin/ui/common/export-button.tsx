import { useState } from 'react'
import { Button } from '@/shared/ui'
import { downloadCsv } from '../../lib/download'
import { errorText } from '../../lib/format'

type Props = {
  path: string
  filename: string
  query?: Record<string, string | number | boolean | undefined>
  label?: string
  disabled?: boolean
}

export function ExportButton({ path, filename, query, label = 'Экспорт CSV', disabled }: Props) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      await downloadCsv(path, filename, query)
    } catch (cause) {
      setError(errorText(cause))
    } finally {
      setBusy(false)
    }
  }

  return (
    <span className="export-button">
      <Button variant="ghost" size="inline" disabled={disabled || busy} onClick={() => void run()}>
        {busy ? 'Готовим…' : label}
      </Button>
      {error && (
        <span className="admin-error" role="alert">
          {error}
        </span>
      )}
    </span>
  )
}
