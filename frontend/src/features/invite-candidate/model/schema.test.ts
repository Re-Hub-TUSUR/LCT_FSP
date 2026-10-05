import { describe, expect, it } from 'vitest'
import { inviteSchema } from './schema'

const valid = {
  message: 'Ищем Go-разработчика в команду платёжного шлюза',
  salaryFrom: '250000',
  salaryTo: '320000',
  contactMethod: '@recruiter',
}

describe('inviteSchema', () => {
  it('coerces salary range to numbers', () => {
    const result = inviteSchema.parse(valid)
    expect(result.salaryFrom).toBe(250000)
    expect(result.salaryTo).toBe(320000)
  })

  it('rejects an inverted salary range', () => {
    const result = inviteSchema.safeParse({ ...valid, salaryFrom: '400000' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['salaryTo'])
  })

  it('requires salary to be set', () => {
    expect(inviteSchema.safeParse({ ...valid, salaryTo: '' }).success).toBe(false)
  })
})
