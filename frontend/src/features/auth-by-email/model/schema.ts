import { z } from 'zod'
import { emailSchema } from '@/shared/lib'

export const PASSWORD_MIN_LENGTH = 8

/** Shown when the sign-up checkbox is left empty, by the form and by «Войти через Яндекс». */
export const TERMS_REQUIRED =
  'Нужно принять Политику конфиденциальности и Пользовательское соглашение'

/** A candidate's consent is a separate document and a separate box (152-ФЗ, ч. 1 ст. 9). */
export const DATA_CONSENT_REQUIRED = 'Нужно согласие на обработку персональных данных'

export const signInSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Введите пароль'),
})

export const signUpSchema = z.object({
  email: emailSchema,
  password: z.string().min(PASSWORD_MIN_LENGTH, `Минимум ${PASSWORD_MIN_LENGTH} символов`),
  personalDataConsent: z.literal(true, TERMS_REQUIRED),
})

export type AuthMode = 'sign-in' | 'sign-up'

export type AuthFormValues = {
  email: string
  password: string
  /** Policy and terms. */
  personalDataConsent: boolean
  /** The candidate's consent to the processing of personal data. */
  dataConsent: boolean
}

export type AuthFieldErrors = Partial<Record<keyof AuthFormValues, string>>

/** `needsDataConsent`: a candidate signs up; an employer's data is processed under the terms. */
export function validateAuthForm(
  mode: AuthMode,
  values: AuthFormValues,
  needsDataConsent = false,
): AuthFieldErrors {
  const schema = mode === 'sign-in' ? signInSchema : signUpSchema
  const result = schema.safeParse({ ...values, email: values.email.trim() })
  const errors: AuthFieldErrors = {}
  if (mode === 'sign-up' && needsDataConsent && !values.dataConsent) {
    errors.dataConsent = DATA_CONSENT_REQUIRED
  }
  if (result.success) return errors

  for (const issue of result.error.issues) {
    const field = issue.path[0] as keyof AuthFormValues | undefined
    if (field && !errors[field]) {
      errors[field] = field === 'email' ? 'Проверьте адрес почты' : issue.message
    }
  }
  return errors
}
