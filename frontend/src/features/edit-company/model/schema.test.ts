import { describe, expect, it } from 'vitest'
import { isValidInn, normalizeWebsite, toCompanyPayload, validateCompany } from './schema'
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
  inn: '7707083893',
  ogrn: '',
  kpp: '773601001',
  legalAddress: '',
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

  it('checks the INN digits and drops the KPP of a sole trader', () => {
    expect(isValidInn('7707083893')).toBe(true)
    expect(isValidInn('500100732259')).toBe(true)
    expect(isValidInn('7707083890')).toBe(false)
    expect(validateCompany({ ...valid, inn: '1234567890' }).inn).toMatch(/ИНН/)
    expect(toCompanyPayload({ ...valid, inn: '500100732259' }).kpp).toBeNull()
  })
})
