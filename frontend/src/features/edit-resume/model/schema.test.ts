import { describe, expect, it } from 'vitest'
import {
  ageOn,
  applyResumeDraft,
  EMPTY_RESUME,
  experienceYearsOf,
  splitList,
  toResumePayload,
  validateResume,
} from './schema'
import type { ResumeValues } from './schema'

const valid: ResumeValues = {
  ...EMPTY_RESUME,
  displayName: 'Иван Иванов',
  headline: 'Backend-разработчик',
  specialization: 'backend',
  city: 'Казань',
  cityId: 551487,
  experienceYears: '4',
  workFormats: ['hybrid'],
  employmentTypes: ['full'],
  stack: ['Python', 'PostgreSQL', 'Docker'],
  telegram: '@ivan',
}

const row = { company: 'Ромашка', position: 'Junior', stack: '' }

describe('validateResume', () => {
  it('asks for the required resume fields', () => {
    const errors = validateResume({
      ...valid,
      displayName: ' ',
      stack: ['Python'],
      workFormats: [],
      employmentTypes: [],
      telegram: '',
    })
    expect(errors.displayName).toBe('Укажите имя и фамилию')
    expect(errors.stack).toBe('Укажите не меньше 3 технологий')
    expect(errors.workFormats).toBe('Выберите формат работы')
    expect(errors.employmentTypes).toBe('Выберите тип занятости')
    expect(errors.phone).toBe('Укажите телефон или Telegram')
  })

  it('accepts a complete resume and strips the telegram mark', () => {
    expect(validateResume(valid)).toEqual({})
    expect(toResumePayload(valid).telegram).toBe('ivan')
    expect(toResumePayload(valid).salaryExpectation).toBeNull()
  })

  it('takes only contacts an employer can use', () => {
    expect(validateResume({ ...valid, phone: '12' }).phone).toBe(
      'Проверьте номер: +7 900 000-00-00',
    )
    expect(validateResume({ ...valid, phone: 'позвоните мне' }).phone).toBeDefined()
    expect(validateResume({ ...valid, phone: '+7 (900) 123-45-67' }).phone).toBeUndefined()
    expect(validateResume({ ...valid, telegram: '!!' }).telegram).toBeDefined()
    // A pasted link is the same username.
    const linked = { ...valid, telegram: 'https://t.me/ivan_dev' }
    expect(validateResume(linked)).toEqual({})
    expect(toResumePayload(linked).telegram).toBe('ivan_dev')
  })

  it('needs years, a place of work or «Нет опыта»', () => {
    expect(validateResume({ ...valid, experienceYears: '' }).experienceYears).toBeDefined()
    expect(validateResume({ ...valid, experienceYears: '', noExperience: true })).toEqual({})
    const payload = toResumePayload({ ...valid, noExperience: true })
    expect(payload.experienceYears).toBe(0)
    expect(payload.experienceEntries).toEqual([])
  })

  it('checks the periods of work', () => {
    const errors = validateResume({
      ...valid,
      experience: [{ ...row, start: '2024-05', end: '2023-01' }],
    })
    expect(errors.experience).toBe('Место работы 1: окончание раньше начала')
  })

  it('rejects candidates under 14 and a wrong GitHub link', () => {
    const young = new Date()
    young.setFullYear(young.getFullYear() - 10)
    const errors = validateResume({
      ...valid,
      birthDate: young.toISOString().slice(0, 10),
      githubUrl: 'gitlab.com/ivan',
    })
    expect(errors.birthDate).toBe('Регистрация доступна с 14 лет')
    expect(errors.githubUrl).toBeDefined()
  })

  it('drops duplicate skills', () => {
    expect(splitList('Python, python, PostgreSQL')).toEqual(['Python', 'PostgreSQL'])
  })
})

describe('experienceYearsOf', () => {
  it('counts overlapping periods once', () => {
    const today = new Date(2026, 0, 15)
    const years = experienceYearsOf(
      [
        { ...row, start: '2020-01', end: '2022-12' },
        { ...row, start: '2022-01', end: '2023-12' },
      ],
      today,
    )
    expect(years).toBe(4)
  })
})

describe('ageOn', () => {
  it('counts the birthday', () => {
    expect(ageOn('2010-06-10', new Date(2026, 5, 9))).toBe(15)
    expect(ageOn('2010-06-10', new Date(2026, 5, 10))).toBe(16)
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
      photo: null,
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
