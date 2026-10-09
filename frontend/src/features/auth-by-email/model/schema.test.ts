import { describe, expect, it } from 'vitest'
import { validateAuthForm } from './schema'

describe('validateAuthForm', () => {
  it('requires consent and a long enough password on sign-up', () => {
    expect(
      validateAuthForm('sign-up', {
        email: 'a@b.ru',
        password: 'short',
        personalDataConsent: false,
      }),
    ).toEqual({
      password: 'Минимум 8 символов',
      personalDataConsent:
        'Нужно принять Политику конфиденциальности и Пользовательское соглашение',
    })
  })

  it('accepts valid sign-in input and trims email', () => {
    expect(
      validateAuthForm('sign-in', {
        email: '  a@b.ru ',
        password: 'x',
        personalDataConsent: false,
      }),
    ).toEqual({})
  })

  it('reports an invalid email', () => {
    expect(
      validateAuthForm('sign-in', { email: 'nope', password: 'x', personalDataConsent: false }),
    ).toEqual({ email: 'Проверьте адрес почты' })
  })
})
