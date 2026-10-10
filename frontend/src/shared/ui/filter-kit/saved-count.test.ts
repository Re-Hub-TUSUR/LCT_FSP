import { describe, expect, it } from 'vitest'
import { savedCountNote } from './filter-kit'

const VACANCIES = ['вакансия', 'вакансии', 'вакансий'] as const

describe('saved search count', () => {
  it('shows the saved count in the whole list', () => {
    expect(savedCountNote(true, 29, 29, 'all', VACANCIES)).toBe('29 вакансий')
    expect(savedCountNote(false, 3, 1, 'all', VACANCIES)).toBe('3 вакансии')
  })

  it('follows the open tab for the open search and stays quiet for the others', () => {
    expect(savedCountNote(true, 29, 1, 'liked', VACANCIES)).toBe('1 вакансия')
    expect(savedCountNote(false, 29, 1, 'liked', VACANCIES)).toBeUndefined()
    expect(savedCountNote(true, 29, undefined, 'liked', VACANCIES)).toBeUndefined()
  })
})
