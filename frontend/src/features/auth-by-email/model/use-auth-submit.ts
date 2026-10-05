import { useMutation } from '@tanstack/react-query'
import { sessionApi, sessionStore } from '@/entities/session'
import type { AuthFormValues, AuthMode } from './schema'

type Role = 'candidate' | 'employer'

/**
 * Sign-in stores the session. Sign-up creates the account and immediately signs in.
 * TODO(auth): once email confirmation is implemented, sign-up must stop at "check your inbox".
 */
export function useAuthSubmit(role: Role, onSuccess: () => void) {
  return useMutation({
    mutationFn: async ({ mode, values }: { mode: AuthMode; values: AuthFormValues }) => {
      const credentials = { email: values.email.trim(), password: values.password }
      if (mode === 'sign-up') {
        await sessionApi.signUp({ ...credentials, role, personalDataConsent: true })
      }
      return sessionApi.signIn(credentials)
    },
    onSuccess: (token) => {
      sessionStore.set({ accessToken: token.accessToken, user: token.user })
      onSuccess()
    },
  })
}
