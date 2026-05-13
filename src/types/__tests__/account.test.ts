import { describe, it, expect } from 'vitest'
import { accountNumberSchema, accountFormSchema } from '../account'

describe('accountNumberSchema', () => {
  it('accepts a valid 10-digit string', () => {
    const result = accountNumberSchema.safeParse('1234567890')
    expect(result.success).toBe(true)
  })

  it('rejects a string that is too short', () => {
    const result = accountNumberSchema.safeParse('12345')
    expect(result.success).toBe(false)
  })

  it('rejects a string that is too long', () => {
    const result = accountNumberSchema.safeParse('12345678901')
    expect(result.success).toBe(false)
  })

  it('rejects non-numeric characters', () => {
    const result = accountNumberSchema.safeParse('abcdefghij')
    expect(result.success).toBe(false)
  })
})

describe('accountFormSchema', () => {
  it('accepts valid form data', () => {
    const result = accountFormSchema.safeParse({ accountNumber: '1234567890' })
    expect(result.success).toBe(true)
  })

  it('rejects invalid form data', () => {
    const result = accountFormSchema.safeParse({ accountNumber: 'abc' })
    expect(result.success).toBe(false)
  })
})
