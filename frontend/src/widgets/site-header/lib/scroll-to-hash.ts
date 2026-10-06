/** Smooth-scroll an in-page landing anchor and keep the hash shareable. */
export function scrollToId(hash: string) {
  const id = hash.startsWith('#') ? hash.slice(1) : hash
  const target = document.getElementById(id)
  if (!target) return
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' })
  document.getElementById(`${id}-title`)?.focus({ preventScroll: true })
  window.history.pushState(null, '', `#${id}`)
}
