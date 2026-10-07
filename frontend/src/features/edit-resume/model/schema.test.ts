import { describe, expect, it } from 'vitest'
import { applyResumeDraft, splitList, toResumePayload, validateResume } from './schema'
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

describe('applyResumeDraft', () => {
  it('fills what the resume says and keeps the rest', () => {
    const next = applyResumeDraft(valid, {
      displayName: 'Пётр Петров',
      headline: null,
      specialization: 'frontend',
      city: ' ',
      experienceYears: 6,
      workFormats: [],
      stack: ['React'],
      softSkills: [],
      about: null,
      salaryExpectation: 250000,
      phone: null,
      telegram: null,
    })
    expect(next).toEqual({
      ...valid,
      displayName: 'Пётр Петров',
      specialization: 'frontend',
      experienceYears: '6',
      stack: ['React'],
      salary: '250000',
    })
  })
})
