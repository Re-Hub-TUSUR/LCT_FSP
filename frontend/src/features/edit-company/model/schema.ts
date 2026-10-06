import type { CompanyDto, CompanyWrite } from '@/entities/company'
import { emailSchema, isHttpUrl } from '@/shared/lib'

export type CompanyValues = {
  name: string
  industry: string
  description: string
  city: string
  size: string
  website: string
  contactEmail: string
}

export type CompanyErrors = Partial<Record<keyof CompanyValues, string>>

export const EMPTY_COMPANY: CompanyValues = {
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

export function normalizeWebsite(value: string): string {
  const trimmed = value.trim()
  if (!trimmed) return ''
  return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`
}

export function validateCompany(values: CompanyValues): CompanyErrors {
  const errors: CompanyErrors = {}
  if (!values.name.trim()) errors.name = 'Укажите название'
  if (!values.industry.trim()) errors.industry = 'Укажите направление'
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
  return {
    name: values.name.trim(),
    industry: values.industry.trim(),
    description: values.description.trim(),
    city: values.city.trim(),
    size: values.size || null,
    website: normalizeWebsite(values.website),
    contactEmail: values.contactEmail.trim(),
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
  }
}
