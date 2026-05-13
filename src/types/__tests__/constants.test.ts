import { describe, it, expect } from 'vitest'
import { ROUTES } from '../routes'
import { MENU_OPTIONS } from '../menu'

describe('ROUTES', () => {
  it('has MAIN_MENU route', () => {
    expect(ROUTES.MAIN_MENU).toBe('/')
  })

  it('has PORTFOLIO_INQUIRY route', () => {
    expect(ROUTES.PORTFOLIO_INQUIRY).toBe('/portfolio-inquiry')
  })

  it('has TRANSACTION_HISTORY route', () => {
    expect(ROUTES.TRANSACTION_HISTORY).toBe('/transaction-history')
  })
})

describe('MENU_OPTIONS', () => {
  it('has 2 options', () => {
    expect(MENU_OPTIONS).toHaveLength(2)
  })

  it('has portfolio option with correct route and shortcut', () => {
    const portfolio = MENU_OPTIONS.find((o) => o.id === 'portfolio')
    expect(portfolio).toBeDefined()
    expect(portfolio!.route).toBe('/portfolio-inquiry')
    expect(portfolio!.shortcut).toBe('1')
  })

  it('has history option with correct route and shortcut', () => {
    const history = MENU_OPTIONS.find((o) => o.id === 'history')
    expect(history).toBeDefined()
    expect(history!.route).toBe('/transaction-history')
    expect(history!.shortcut).toBe('2')
  })
})
