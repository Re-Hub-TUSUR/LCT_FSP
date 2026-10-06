import { describe, expect, it } from 'vitest'
import { splitList, toResumePayload, validateResume } from './schema'
import type { ResumeValues } from './schema'

const valid: ResumeValues = {
  displayName: 'Иван Иванов',
  headline: 'Backend-разработчик',
  specialization: 'backend',
  city: 'Казань',
  experienceYears: '4',
  workFormats: ['hybrid'],
  stack: ['Python', 'PostgreSQL'],
  softSkills: [],
  about: '',
  phone: '',
  telegram: '@ivan',
  salary: '',
}

describe('validateResume', () => {
  it('asks for the required resume fields', () => {
    const errors = validateResume({ ...valid, displayName: ' ', stack: [], workFormats: [] })
    expect(errors.displayName).toBe('Укажите имя и фамилию')
    expect(errors.stack).toBe('Укажите хотя бы один навык')
    expect(errors.workFormats).toBe('Выберите формат работы')
  })

  it('accepts a complete resume and strips the telegram mark', () => {
    expect(validateResume(valid)).toEqual({})
    expect(toResumePayload(valid).telegram).toBe('ivan')
    expect(toResumePayload(valid).stack).toEqual(['Python', 'PostgreSQL'])
    expect(toResumePayload(valid).salaryExpectation).toBeNull()
  })

  it('drops duplicate skills', () => {
    expect(splitList('Python, python, PostgreSQL')).toEqual(['Python', 'PostgreSQL'])
  })
})
