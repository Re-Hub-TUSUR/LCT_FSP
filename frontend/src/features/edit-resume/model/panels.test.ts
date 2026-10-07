import { describe, expect, it } from 'vitest'
import { changedPanels, panelsPayload, validatePanels } from './panels'
import { EMPTY_RESUME } from './schema'
import type { ResumeValues } from './schema'

const FILLED: ResumeValues = {
  ...EMPTY_RESUME,
  displayName: 'Анна Петрова',
  headline: 'Backend-разработчик',
  specialization: 'backend',
  city: 'Казань',
  workFormats: ['remote'],
  employmentTypes: ['full'],
  experienceYears: '3',
  stack: ['Python', 'FastAPI', 'PostgreSQL'],
  phone: '+7 900 000-00-00',
}

describe('resume panels', () => {
  it('reports only the errors of the open panel', () => {
    const values = { ...FILLED, city: '', stack: ['Python'] }
    expect(validatePanels(values, ['skills'])).toEqual({
      stack: 'Укажите не меньше 3 технологий',
    })
    expect(validatePanels(values, ['basic'])).toEqual({ city: 'Укажите город' })
    expect(validatePanels(FILLED, ['basic', 'skills', 'contacts'])).toEqual({})
  })

  it('sends only the columns of the saved panels', () => {
    expect(panelsPayload(FILLED, ['skills'])).toEqual({
      stack: ['Python', 'FastAPI', 'PostgreSQL'],
      softSkills: [],
    })
    expect(panelsPayload({ ...FILLED, telegram: '@anna' }, ['contacts'])).toEqual({
      phone: '+7 900 000-00-00',
      telegram: 'anna',
      githubUrl: null,
    })
  })

  it('opens the panels a recognised resume changed', () => {
    const after = { ...FILLED, city: 'Москва', about: 'Пишу сервисы' }
    expect(changedPanels(FILLED, after)).toEqual(['basic', 'about'])
    expect(changedPanels(FILLED, { ...FILLED })).toEqual([])
  })
})
