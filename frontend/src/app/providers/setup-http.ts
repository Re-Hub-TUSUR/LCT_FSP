import { refreshSession, sessionStore } from '@/entities/session'
import { configureHttp } from '@/shared/api'

/** Connects the infrastructure HTTP client to the session entity (shared can't import entities). */
export function setupHttp() {
  configureHttp({
    getAccessToken: () => sessionStore.getSnapshot()?.accessToken ?? null,
    onUnauthorized: () => sessionStore.clear(),
    refresh: () => refreshSession(),
  })
}
