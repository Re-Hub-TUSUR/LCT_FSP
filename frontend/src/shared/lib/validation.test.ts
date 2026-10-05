import { describe, expect, it } from 'vitest'
import { isEmail, isHttpUrl, isSafeInternalPath } from './validation'

describe('validation helpers', () => {
  it('validates emails', () => {
    expect(isEmail('dev@fsp.ru')).toBe(true)
    expect(isEmail('dev@')).toBe(false)
  })

  it('accepts only same-app redirect paths', () => {
    expect(isSafeInternalPath('/profile?tab=1')).toBe(true)
    expect(isSafeInternalPath('//evil.example')).toBe(false)
    expect(isSafeInternalPath('/\\evil.example')).toBe(false)
    expect(isSafeInternalPath('https://evil.example')).toBe(false)
    expect(isSafeInternalPath(null)).toBe(false)
  })

  it('accepts only http(s) links', () => {
    expect(isHttpUrl('https://fsp-russia.ru')).toBe(true)
    expect(isHttpUrl('javascript:alert(1)')).toBe(false)
    expect(isHttpUrl('not a url')).toBe(false)
  })
})
