import { describe, expect, it } from 'vitest'
import { isAdminHost } from '@/shared/config'

describe('isAdminHost', () => {
  it('matches the admin subdomain and nothing else', () => {
    expect(isAdminHost('admin.localhost')).toBe(true)
    expect(isAdminHost('admin.xn----7sbbqrfj4cm0h.xn--p1ai')).toBe(true)
    expect(isAdminHost('localhost', '8082')).toBe(true)
    expect(isAdminHost('localhost')).toBe(false)
    expect(isAdminHost('localhost', '8080')).toBe(false)
    expect(isAdminHost('administrator.example.com')).toBe(false)
  })
})
