const RELOADED_AT = 'kadry:stale-build-reload'
/** One automatic reload per minute: a chunk that is still missing after it is a real failure. */
const COOLDOWN = 60_000

/**
 * After a deploy an open tab still asks for the chunks of the previous build, and they are gone.
 * Chrome, Firefox and Safari word this failure differently.
 */
export function isStaleChunkError(error: unknown): boolean {
  if (!(error instanceof Error)) return false
  return /dynamically imported module|importing a module script failed|unable to preload css/i.test(
    error.message,
  )
}

/** False when a reload has just been tried, or the tab has no storage to remember that it was. */
export function canReloadForNewBuild(): boolean {
  try {
    return Date.now() - Number(sessionStorage.getItem(RELOADED_AT) ?? 0) >= COOLDOWN
  } catch {
    return false
  }
}

/** Reloads the page to pick up the new build; false when it has just been tried. */
export function reloadForNewBuild(): boolean {
  if (!canReloadForNewBuild()) return false
  try {
    sessionStorage.setItem(RELOADED_AT, String(Date.now()))
  } catch {
    return false
  }
  window.location.reload()
  return true
}
