import { describe, expect, it } from 'vitest'
import { toggleGrade, toVacancyPayload, validateVacancy } from './schema'
import type { VacancyValues } from './schema'

const valid: VacancyValues = {
  title: 'Backend-разработчик',
  specialization: 'backend',
  grades: ['middle'],
  description: 'О'.repeat(150),
  stackRequired: ['Python', 'PostgreSQL'],
  stackNice: ['Kafka', 'python'],
  salaryFrom: '200 000',
  salaryTo: '320 000',
  workFormat: 'hybrid',
  city: ' Москва ',
  relocationHelp: true,
  employmentTypes: ['full'],
  benefits: ['dms'],
  verifiedGradeOnly: true,
  fspBestResult: '',
  fspDiscipline: 'algorithmic',
  minExperienceYears: 1,
}

describe('validateVacancy', () => {
  it('accepts a complete vacancy', () => {
    expect(validateVacancy(valid)).toEqual({})
  })

  it('asks for a city unless the work is remote', () => {
    expect(validateVacancy({ ...valid, city: ' ' }).city).toMatch(/город/)
    expect(validateVacancy({ ...valid, city: '', workFormat: 'remote' })).toEqual({})
  })

  it('checks the salary range, the description and the required stack', () => {
    expect(validateVacancy({ ...valid, salaryFrom: '400000' }).salaryTo).toMatch(/меньше/)
    expect(validateVacancy({ ...valid, salaryFrom: '' }).salaryFrom).toBeDefined()
    expect(validateVacancy({ ...valid, description: 'коротко' }).description).toMatch(/ещё 143/)
    expect(validateVacancy({ ...valid, stackRequired: [] }).stackRequired).toBeDefined()
    expect(validateVacancy({ ...valid, grades: [] }).grades).toBeDefined()
  })
})

describe('toggleGrade', () => {
  it('joins a neighbouring grade and replaces the choice with a distant one', () => {
    expect(toggleGrade([], 'middle')).toEqual(['middle'])
    expect(toggleGrade(['senior'], 'middle')).toEqual(['middle', 'senior'])
    expect(toggleGrade(['junior'], 'senior')).toEqual(['senior'])
    expect(toggleGrade(['middle', 'senior'], 'lead')).toEqual(['lead'])
    expect(toggleGrade(['middle', 'senior'], 'middle')).toEqual(['senior'])
  })
})

describe('toVacancyPayload', () => {
  it('reads the salary, trims the city and keeps a technology in one list', () => {
    const payload = toVacancyPayload(valid, false)
    expect(payload.salary).toEqual({ from: 200_000, to: 320_000 })
    expect(payload.city).toBe('Москва')
    expect(payload.stackNice).toEqual(['Kafka'])
    expect(payload.fspDiscipline).toBeNull()
    expect(payload.publish).toBe(false)
  })

  it('drops the office details of a remote vacancy', () => {
    const payload = toVacancyPayload({ ...valid, workFormat: 'remote' }, true)
    expect([payload.city, payload.relocationHelp]).toEqual([null, false])
  })
})
