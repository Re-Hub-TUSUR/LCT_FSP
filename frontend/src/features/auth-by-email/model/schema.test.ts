import { describe, expect, it } from 'vitest'
import { validateAuthForm } from './schema'

describe('validateAuthForm', () => {
  it('requires consent and a long enough password on sign-up', () => {
    expect(
      validateAuthForm('sign-up', {
        email: 'a@b.ru',
        password: 'short',
        personalDataConsent: false,
        dataConsent: false,
      }),
    ).toEqual({
      password: 'Минимум 8 символов',
      personalDataConsent:
        'Нужно принять Политику конфиденциальности и Пользовательское соглашение',
    })
  })

  it('asks a candidate for the separate consent to process personal data', () => {
    const values = {
      email: 'a@b.ru',
      password: 'long-enough',
      personalDataConsent: true,
      dataConsent: false,
    }
    expect(validateAuthForm('sign-up', values, true)).toEqual({
      dataConsent: 'Нужно согласие на обработку персональных данных',
    })
    expect(validateAuthForm('sign-up', { ...values, dataConsent: true }, true)).toEqual({})
  })

  it('accepts valid sign-in input and trims email', () => {
    expect(
      validateAuthForm('sign-in', {
        email: '  a@b.ru ',
        password: 'x',
        personalDataConsent: false,
        dataConsent: false,
      }),
    ).toEqual({})
  })

  it('reports an invalid email', () => {
    expect(
      validateAuthForm('sign-in', {
        email: 'nope',
        password: 'x',
        personalDataConsent: false,
        dataConsent: false,
      }),
    ).toEqual({ email: 'Проверьте адрес почты' })
  })
})
