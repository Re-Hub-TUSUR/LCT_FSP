import { http } from '@/shared/api'

type Query = Record<string, string | number | boolean | undefined>

/** Hands the browser a file the API produced (CSV export, a PDF document). */
export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  // Revoked on the next tick: some browsers start the download asynchronously.
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

/** Downloads an admin CSV export with the session's token. */
export async function downloadCsv(path: string, filename: string, query: Query = {}) {
  const blob = await http.blob(path, { query })
  saveBlob(blob, filename)
}

/** Opens a PDF in a new tab: the request needs the token, so it goes through a blob URL. */
export function openPdf(blob: Blob) {
  const url = URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }))
  window.open(url, '_blank', 'noopener')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
