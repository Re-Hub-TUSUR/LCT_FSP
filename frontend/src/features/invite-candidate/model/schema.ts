import { z } from 'zod'

const salary = z.coerce
  .number<string>({ error: 'Укажите сумму' })
  .int('Целое число')
  .positive('Сумма должна быть больше нуля')

/** Salary range is mandatory in every invitation (ТЗ 2.2, items 1–2). */
export const inviteSchema = z
  .object({
    message: z.string().trim().min(20, 'Опишите предложение (от 20 символов)').max(4000),
    salaryFrom: salary,
    salaryTo: salary,
    contactMethod: z.string().trim().min(3, 'Укажите способ связи'),
  })
  .refine((v) => v.salaryFrom <= v.salaryTo, {
    path: ['salaryTo'],
    message: 'Верхняя граница меньше нижней',
  })

export type InviteFormValues = z.input<typeof inviteSchema>
export type InviteFormErrors = Partial<Record<keyof InviteFormValues, string>>
