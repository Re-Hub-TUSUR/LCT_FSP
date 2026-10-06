const urls = new Map<string, string>()

/** One object URL per profile for this tab. Replaced photos drop the previous URL. */
export function cachePhotoUrl(id: string, blob: Blob): string {
  const known = urls.get(id)
  if (known) return known
  const created = URL.createObjectURL(blob)
  urls.set(id, created)
  return created
}

export function dropPhotoUrl(id: string) {
  const known = urls.get(id)
  if (!known) return
  URL.revokeObjectURL(known)
  urls.delete(id)
}
