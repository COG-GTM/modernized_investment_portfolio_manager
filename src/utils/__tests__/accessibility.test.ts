import { describe, it, expect, vi } from 'vitest'
import { focusElement, trapFocus, generateAriaLabel } from '../accessibility'

describe('focusElement', () => {
  it('calls focus() and scrollIntoView() on the element', () => {
    const element = document.createElement('button')
    element.focus = vi.fn()
    element.scrollIntoView = vi.fn()

    focusElement(element)

    expect(element.focus).toHaveBeenCalled()
    expect(element.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest',
    })
  })

  it('handles null gracefully', () => {
    expect(() => focusElement(null)).not.toThrow()
  })
})

describe('generateAriaLabel', () => {
  it('returns label only', () => {
    expect(generateAriaLabel('Save')).toBe('Save')
  })

  it('includes shortcut', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S')).toBe('Save - Press Ctrl+S')
  })

  it('includes description', () => {
    expect(generateAriaLabel('Save', undefined, 'Saves the document')).toBe(
      'Save - Saves the document'
    )
  })

  it('includes both shortcut and description', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S', 'Saves the document')).toBe(
      'Save - Press Ctrl+S - Saves the document'
    )
  })
})

describe('trapFocus', () => {
  it('wraps Tab from last to first element', () => {
    const container = document.createElement('div')
    const button1 = document.createElement('button')
    const button2 = document.createElement('button')
    button1.textContent = 'First'
    button2.textContent = 'Last'
    container.appendChild(button1)
    container.appendChild(button2)
    document.body.appendChild(container)

    button1.focus = vi.fn()
    button2.focus = vi.fn()

    const cleanup = trapFocus(container)

    // Simulate Tab on last element
    Object.defineProperty(document, 'activeElement', {
      value: button2,
      writable: true,
      configurable: true,
    })
    const tabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true,
      cancelable: true,
    })
    container.dispatchEvent(tabEvent)

    expect(button1.focus).toHaveBeenCalled()

    cleanup()
    document.body.removeChild(container)
  })

  it('wraps Shift+Tab from first to last element', () => {
    const container = document.createElement('div')
    const button1 = document.createElement('button')
    const button2 = document.createElement('button')
    button1.textContent = 'First'
    button2.textContent = 'Last'
    container.appendChild(button1)
    container.appendChild(button2)
    document.body.appendChild(container)

    button1.focus = vi.fn()
    button2.focus = vi.fn()

    const cleanup = trapFocus(container)

    // Simulate Shift+Tab on first element
    Object.defineProperty(document, 'activeElement', {
      value: button1,
      writable: true,
      configurable: true,
    })
    const shiftTabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true,
      cancelable: true,
    })
    container.dispatchEvent(shiftTabEvent)

    expect(button2.focus).toHaveBeenCalled()

    cleanup()
    document.body.removeChild(container)
  })
})
