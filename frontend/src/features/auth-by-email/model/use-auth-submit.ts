import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { sessionApi, sessionStore } from '@/entities/session'
import { ApiError } from '@/shared/api'
import type { AuthFormValues, AuthMode } from './schema'

type Role = 'candidate' | 'employer'

type PendingVerification = {
  email: string
  password: string
}

type AuthResult =
  | { kind: 'session'; token: Awaited<ReturnType<typeof sessionApi.signIn>> }
  | ({ kind: 'verify' } & PendingVerification)

/**
 * Sign-in stores the session. Sign-up and an unverified sign-in stop at the email code,
 * then sign in once the code is confirmed.
 */
export function useAuthSubmit(role: Role, onSuccess: () => void) {
  const [verification, setVerification] = useState<PendingVerification | null>(null)

  const submit = useMutation({
    mutationFn: async ({
      mode,
      values,
    }: {
      mode: AuthMode
      values: AuthFormValues
    }): Promise<AuthResult> => {
      const credentials = { email: values.email.trim(), password: values.password }
      if (mode === 'sign-up') {
        await sessionApi.signUp({ ...credentials, role, personalDataConsent: true })
        return { kind: 'verify', ...credentials }
      }
      try {
        const token = await sessionApi.signIn(credentials)
        return { kind: 'session', token }
      } catch (error) {
        if (error instanceof ApiError && error.code === 'email_not_verified') {
          return { kind: 'verify', ...credentials }
        }
        throw error
      }
    },
    onSuccess: (result) => {
      if (result.kind === 'verify') {
        setVerification({ email: result.email, password: result.password })
        return
      }
      sessionStore.set({ accessToken: result.token.accessToken, user: result.token.user })
      onSuccess()
    },
  })

  const finishVerification = async () => {
    if (!verification) return
    const token = await sessionApi.signIn({
      email: verification.email,
      password: verification.password,
    })
    sessionStore.set({ accessToken: token.accessToken, user: token.user })
    setVerification(null)
    onSuccess()
  }

  return {
    submit,
    verification,
    closeVerification: () => setVerification(null),
    finishVerification,
  }
}
