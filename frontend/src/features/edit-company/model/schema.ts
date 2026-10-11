import type { CompanyDto, CompanyWrite } from '@/entities/company'
import { emailSchema, isHttpUrl } from '@/shared/lib'

export type LegalValues = {
  inn: string
  ogrn: string
  kpp: string
  legalAddress: string
}

export type CompanyValues = LegalValues & {
  name: string
  industry: string
  description: string
  city: string
  size: string
  website: string
  contactEmail: string
}

export type CompanyErrors = Partial<Record<keyof CompanyValues, string>>
export type LegalErrors = Partial<Record<keyof LegalValues, string>>

export const EMPTY_LEGAL: LegalValues = { inn: '', ogrn: '', kpp: '', legalAddress: '' }

export const EMPTY_COMPANY: CompanyValues = {
  ...EMPTY_LEGAL,
  name: '',
  industry: '',
  description: '',
  city: '',
  size: '',
  website: '',
  contactEmail: '',
}

export const COMPANY_SIZES = [
  { value: '', label: 'Не указан' },
  { value: '1-10', label: '1–10' },
  { value: '11-50', label: '11–50' },
  { value: '51-200', label: '51–200' },
  { value: '201-500', label: '201–500' },
  { value: '500+', label: '500+' },
] as const

export const INDUSTRIES = [
  'Финтех',
  'E-commerce',
  'Телеком',
  'Госсектор',
  'Образование',
  'Медицина',
  'Игровая индустрия',
  'Промышленность',
] as const

export const DESCRIPTION_MIN = 100
export const DESCRIPTION_MAX = 3000

const TEN = [2, 4, 10, 3, 5, 9, 4, 6, 8]
const ELEVEN = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
const TWELVE = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]

function checkDigit(digits: number[], weights: number[]): number {
  return (weights.reduce((sum, weight, index) => sum + weight * (digits[index] ?? 0), 0) % 11) % 10
}

const hasInnLength = (value: string) => /^\d{10}(\d{2})?$/.test(value)

/** 10 digits for an organisation, 12 for a sole trader; the check digits must match. */
export function isValidInn(value: string): boolean {
  if (!hasInnLength(value)) return false
  const digits = [...value].map(Number)
  if (digits.length === 10) return checkDigit(digits, TEN) === digits[9]
  return checkDigit(digits, ELEVEN) === digits[10] && checkDigit(digits, TWELVE) === digits[11]
}

const digitsOnly = (value: string) => value.replace(/\s+/g, '')

export function normalizeWebsite(value: string): string {
  const trimmed = value.trim()
  if (!trimmed) return ''
  return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`
}

export function validateLegal(values: LegalValues): LegalErrors {
  const errors: LegalErrors = {}
  const inn = digitsOnly(values.inn)
  if (!inn) errors.inn = 'Укажите ИНН'
  else if (!hasInnLength(inn)) errors.inn = 'ИНН: 10 или 12 цифр'
  else if (!isValidInn(inn)) errors.inn = 'Проверьте ИНН: не сходится контрольная цифра'
  const ogrn = digitsOnly(values.ogrn)
  if (ogrn && !/^(\d{13}|\d{15})$/.test(ogrn)) errors.ogrn = 'ОГРН: 13 цифр, ОГРНИП: 15'
  const kpp = digitsOnly(values.kpp)
  if (kpp && !/^\d{9}$/.test(kpp)) errors.kpp = 'КПП: 9 цифр'
  return errors
}

export function validateCompany(values: CompanyValues): CompanyErrors {
  const errors: CompanyErrors = validateLegal(values)
  if (!values.name.trim()) errors.name = 'Укажите название'
  if (!INDUSTRIES.includes(values.industry as (typeof INDUSTRIES)[number])) {
    errors.industry = 'Выберите направление из списка'
  }
  const description = values.description.trim()
  if (description.length < DESCRIPTION_MIN) {
    errors.description = `Опишите компанию: ещё ${DESCRIPTION_MIN - description.length} символов`
  } else if (description.length > DESCRIPTION_MAX) {
    errors.description = `Не больше ${DESCRIPTION_MAX} символов`
  }
  if (!values.city.trim()) errors.city = 'Укажите город'
  const website = normalizeWebsite(values.website)
  if (!website || !isHttpUrl(website)) errors.website = 'Проверьте адрес сайта'
  if (!emailSchema.safeParse(values.contactEmail.trim()).success) {
    errors.contactEmail = 'Проверьте почту для кандидатов'
  }
  return errors
}

export function toCompanyPayload(values: CompanyValues): CompanyWrite {
  const inn = digitsOnly(values.inn)
  return {
    name: values.name.trim(),
    industry: values.industry.trim(),
    description: values.description.trim(),
    city: values.city.trim(),
    size: values.size || null,
    website: normalizeWebsite(values.website),
    contactEmail: values.contactEmail.trim(),
    inn,
    ogrn: digitsOnly(values.ogrn) || null,
    // A sole trader (12-digit INN) has no KPP.
    kpp: inn.length === 10 ? digitsOnly(values.kpp) || null : null,
    legalAddress: values.legalAddress.trim() || null,
  }
}

export function companyValuesFrom(company: CompanyDto | null): CompanyValues {
  if (!company) return EMPTY_COMPANY
  return {
    name: company.name,
    industry: company.industry ?? '',
    description: company.description ?? '',
    city: company.city ?? '',
    size: company.size ?? '',
    website: company.website ?? '',
    contactEmail: company.contactEmail ?? '',
    inn: company.inn ?? '',
    ogrn: company.ogrn ?? '',
    kpp: company.kpp ?? '',
    legalAddress: company.legalAddress ?? '',
  }
}
