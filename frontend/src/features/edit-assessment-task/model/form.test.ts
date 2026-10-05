import { describe, expect, it } from 'vitest'
import { toFormValues, toPayload, validateTask } from './form'

describe('assessment task form', () => {
  it('builds a quiz payload with the question as its title', () => {
    const values = {
      ...toFormValues('quiz'),
      statement: '  Что вернёт 17 % 5?  ',
      topic: 'algorithms',
      options: ['2', '3', '5', '7'],
    }

    expect(validateTask(values)).toBeNull()
    expect(toPayload(values)).toMatchObject({
      kind: 'quiz',
      title: 'Что вернёт 17 % 5?',
      quiz: { options: ['2', '3', '5', '7'], correct: [0], multiple: false },
      code: null,
    })
  })

  it('requires both an open and a hidden test group for a code task', () => {
    const values = {
      ...toFormValues('code'),
      title: 'Эхо',
      statement: 'Выведите ввод.',
      topic: 'io',
      groups: [
        { input: 'a', expected: 'a', hidden: false },
        { input: 'b', expected: 'b', hidden: false },
      ],
    }

    expect(validateTask(values)).toMatch(/открытая и одна закрытая/)
  })

  it('rejects an expected output the code runner would cut', () => {
    const values = {
      ...toFormValues('code'),
      title: 'Эхо',
      statement: 'Выведите ввод.',
      topic: 'io',
      groups: [
        { input: 'a', expected: 'x'.repeat(901), hidden: false },
        { input: 'b', expected: 'b', hidden: true },
      ],
    }

    expect(validateTask(values)).toMatch(/900/)
  })

  it('omits an empty reference solution', () => {
    const values = {
      ...toFormValues('code'),
      title: 'Эхо',
      statement: 'Выведите ввод.',
      topic: 'io',
      groups: [
        { input: 'a', expected: 'a', hidden: false },
        { input: 'b', expected: 'b', hidden: true },
      ],
    }

    expect(validateTask(values)).toBeNull()
    expect(toPayload(values).code?.reference).toBeNull()
  })
})
