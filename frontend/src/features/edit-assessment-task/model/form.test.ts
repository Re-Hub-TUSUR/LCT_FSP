import { describe, expect, it } from 'vitest'
import { toFormValues, toPayload, validateTask } from './form'
import type { TaskFormValues } from './form'

const codeTask = (code: Partial<TaskFormValues['code']>): TaskFormValues => {
  const values = toFormValues('code')
  return {
    ...values,
    title: 'Эхо',
    statement: 'Выведите ввод.',
    topic: 'io',
    code: { ...values.code, ...code },
  }
}

describe('assessment task form', () => {
  it('builds a quiz payload with the question as its title', () => {
    const empty = toFormValues('quiz')
    const values = {
      ...empty,
      statement: '  Что вернёт 17 % 5?  ',
      topic: 'algorithms',
      quiz: { ...empty.quiz, options: ['2', ' 3 ', '5', '7'] },
    }

    expect(validateTask(values)).toBeNull()
    expect(toPayload(values)).toMatchObject({
      kind: 'quiz',
      title: 'Что вернёт 17 % 5?',
      payload: { options: ['2', '3', '5', '7'], correct: [0], multiple: false },
    })
  })

  it('requires both an open and a hidden test group for a code task', () => {
    const values = codeTask({
      groups: [
        { input: 'a', expected: 'a', hidden: false },
        { input: 'b', expected: 'b', hidden: false },
      ],
    })

    expect(validateTask(values)).toMatch(/открытая и одна закрытая/)
  })

  it('rejects an expected output the code runner would cut', () => {
    const values = codeTask({
      groups: [
        { input: 'a', expected: 'x'.repeat(901), hidden: false },
        { input: 'b', expected: 'b', hidden: true },
      ],
    })

    expect(validateTask(values)).toMatch(/900/)
  })

  it('omits an empty reference solution', () => {
    const values = codeTask({
      groups: [
        { input: 'a', expected: 'a', hidden: false },
        { input: 'b', expected: 'b', hidden: true },
      ],
    })

    expect(validateTask(values)).toBeNull()
    expect(toPayload(values)).toMatchObject({ kind: 'code', payload: { reference: null } })
  })

  it('builds an open question with reviewer notes and its own title', () => {
    const empty = toFormValues('open')
    const values = {
      ...empty,
      statement: 'Опишите, как спроектируете очередь задач.',
      topic: 'design',
      open: { maxLength: '1500', guidance: ' Ретраи, идемпотентность ' },
    }

    expect(validateTask(values)).toBe('Укажите название задачи')
    expect(
      validateTask({ ...values, title: 'Очередь', open: { ...values.open, maxLength: '50' } }),
    ).toMatch(/от 100/)
    expect(toPayload({ ...values, title: ' Очередь ' })).toMatchObject({
      kind: 'open',
      title: 'Очередь',
      payload: { maxLength: 1500, guidance: 'Ретраи, идемпотентность' },
    })
  })

  it('opens an existing task with the content of its kind', () => {
    const values = toFormValues('open', {
      id: 't1',
      platform: false,
      createdAt: '2026-10-07T10:00:00Z',
      kind: 'open',
      difficulty: 'medium',
      specializations: [],
      topic: 'design',
      title: 'Очередь',
      statement: 'Опишите очередь.',
      isActive: true,
      payload: { maxLength: 800, guidance: null },
    })

    expect(values.open).toEqual({ maxLength: '800', guidance: '' })
    expect(values.quiz.options).toHaveLength(4)
  })
})
