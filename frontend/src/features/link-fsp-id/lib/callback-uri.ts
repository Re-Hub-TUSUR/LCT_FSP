import { ROUTES } from '@/shared/config'

/** Must match a redirect URI registered for the platform's FSP ID client. */
export function fspCallbackUri(): string {
  return `${window.location.origin}${ROUTES.fspCallback}`
}

/** A full page load: FSP ID is another site. */
export function goToFspId(authorizeUrl: string): void {
  window.location.assign(authorizeUrl)
}
