import { z } from 'zod'
import { emailSchema } from '@/shared/lib'

export const PASSWORD_MIN_LENGTH = 8

export const signInSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Введите пароль'),
})

export const signUpSchema = z.object({
  email: emailSchema,
  password: z.string().min(PASSWORD_MIN_LENGTH, `Минимум ${PASSWORD_MIN_LENGTH} символов`),
  personalDataConsent: z.literal(
    true,
    'Нужно принять Политику конфиденциальности и Пользовательское соглашение',
  ),
})

export type AuthMode = 'sign-in' | 'sign-up'

export type AuthFormValues = {
  email: string
  password: string
  personalDataConsent: boolean
}

export type AuthFieldErrors = Partial<Record<keyof AuthFormValues, string>>

export function validateAuthForm(mode: AuthMode, values: AuthFormValues): AuthFieldErrors {
  const schema = mode === 'sign-in' ? signInSchema : signUpSchema
  const result = schema.safeParse({ ...values, email: values.email.trim() })
  if (result.success) return {}

  const errors: AuthFieldErrors = {}
  for (const issue of result.error.issues) {
    const field = issue.path[0] as keyof AuthFormValues | undefined
    if (field && !errors[field]) {
      errors[field] = field === 'email' ? 'Проверьте адрес почты' : issue.message
    }
  }
  return errors
}
