import { describe, expect, it } from 'vitest'
import { emptyForm, toPayload, undeclared, validate } from './task-form'
import type { TaskForm } from './task-form'

function quiz(patch: Partial<TaskForm> = {}): TaskForm {
  return {
    ...emptyForm('quiz'),
    title: 'Сумма',
    statement: 'Сколько будет {a} + {b}?',
    skill: 'arithmetic',
    variables: [
      { name: 'a', min: '1', max: '9', step: '1' },
      { name: 'b', min: '1', max: '9', step: '1' },
    ],
    options: [
      { text: '{a}', correct: true },
      { text: 'другое', correct: false },
      { text: '', correct: false },
    ],
    ...patch,
  }
}

describe('task form', () => {
  it('accepts a complete quiz and drops empty options', () => {
    const form = quiz()
    expect(validate(form)).toBeNull()
    expect(toPayload(form).payload).toEqual({
      options: ['{a}', 'другое'],
      correct: [0],
      multiple: false,
    })
  })

  it('finds placeholders without a variable', () => {
    const form = quiz({ statement: '{a} + {c} + {c}', variables: [quiz().variables[0]!] })
    expect(undeclared(form)).toEqual(['c'])
    expect(validate(form)).toMatch(/необъявленные переменные: c/)
  })

  it('checks variable ranges', () => {
    const reversed = quiz({ variables: [{ name: 'a', min: '5', max: '1', step: '1' }] })
    const badName = quiz({ variables: [{ name: '1a', min: '1', max: '2', step: '1' }] })
    const zeroStep = quiz({ variables: [{ name: 'a', min: '1', max: '2', step: '0' }] })
    expect(validate({ ...reversed, statement: '{a}', options: quiz().options })).toMatch(/больше/)
    expect(validate(badName)).toMatch(/латиница/)
    expect(validate({ ...zeroStep, statement: '{a}' })).toMatch(/шаг/)
  })

  it('requires one correct option in a single-choice question', () => {
    const none = quiz({
      options: [
        { text: 'а', correct: false },
        { text: 'б', correct: false },
      ],
    })
    const two = quiz({
      options: [
        { text: 'а', correct: true },
        { text: 'б', correct: true },
      ],
    })
    expect(validate({ ...none, statement: 'x', variables: [] })).toMatch(/правильный/)
    expect(validate({ ...two, statement: 'x', variables: [] })).toMatch(/один/)
    expect(validate({ ...two, statement: 'x', variables: [], multiple: true })).toBeNull()
  })

  it('needs open and hidden test cases for code', () => {
    const base = { ...emptyForm('code'), title: 'Эхо', statement: 'Выведите ввод', skill: 'io' }
    const open = {
      ...base,
      groups: [
        { input: '1', expected: '1', hidden: false },
        { input: '2', expected: '2', hidden: false },
      ],
    }
    const ok = {
      ...base,
      languages: 'python-3.14, go',
      groups: [
        { input: '1', expected: '1', hidden: false },
        { input: '2', expected: '2', hidden: true },
      ],
    }
    expect(validate(open)).toMatch(/скрытый/)
    expect(validate(ok)).toBeNull()
    expect(toPayload(ok).payload).toMatchObject({ languages: ['python-3.14', 'go'], timeLimit: 5 })
  })

  it('edits one starter and keeps the starters of other languages', () => {
    const base = {
      ...emptyForm('code'),
      title: 'Эхо',
      statement: 'Выведите ввод',
      skill: 'io',
      groups: [
        { input: '1', expected: '1', hidden: false },
        { input: '2', expected: '2', hidden: true },
      ],
      starterOther: { 'go-1.26': 'package main' },
    }
    const filled = { ...base, starterLanguage: 'python-3.14', starterCode: 'print(1)' }

    expect(validate({ ...base, starterCode: 'print(1)' })).toMatch(/Стартовый код/)
    expect(validate(filled)).toBeNull()
    expect(toPayload(filled).payload).toMatchObject({
      starter: { 'go-1.26': 'package main', 'python-3.14': 'print(1)' },
    })
    const heavy = [
      { input: '1', expected: '1', hidden: false },
      { input: '2', expected: '2', hidden: true, weight: 11 },
    ]
    expect(validate({ ...filled, groups: heavy })).toMatch(/Вес/)
  })

  it('sends the time limit and grade only when set', () => {
    expect(toPayload(quiz()).timeLimitMinutes).toBeNull()
    expect(toPayload(quiz()).grade).toBeNull()
    expect(toPayload(quiz({ timeLimitMinutes: '15', grade: 'middle' }))).toMatchObject({
      timeLimitMinutes: 15,
      grade: 'middle',
    })
    expect(validate(quiz({ timeLimitMinutes: '0' }))).toMatch(/Лимит/)
  })
})
