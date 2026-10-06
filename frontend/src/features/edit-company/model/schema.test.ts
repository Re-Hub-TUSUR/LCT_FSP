import { describe, expect, it } from 'vitest'
import { normalizeWebsite, toCompanyPayload, validateCompany } from './schema'
import type { CompanyValues } from './schema'

const description = 'П'.repeat(100)

const valid: CompanyValues = {
  name: 'ООО «Технологии»',
  industry: 'Финтех',
  description,
  city: 'Москва',
  size: '11-50',
  website: 'company.example',
  contactEmail: 'hr@company.example',
}

describe('validateCompany', () => {
  it('requires a description of at least 100 characters', () => {
    expect(validateCompany({ ...valid, description: 'коротко' }).description).toMatch(/ещё/)
  })

  it('adds https and accepts a complete profile', () => {
    expect(validateCompany(valid)).toEqual({})
    expect(normalizeWebsite('company.example')).toBe('https://company.example')
    expect(toCompanyPayload(valid).website).toBe('https://company.example')
    expect(toCompanyPayload({ ...valid, size: '' }).size).toBeNull()
  })
})
