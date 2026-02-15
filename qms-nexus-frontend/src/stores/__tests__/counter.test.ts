import { describe, it, expect } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCounterStore } from '../counter'

describe('Counter Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with correct default values', () => {
    const counter = useCounterStore()
    
    expect(counter.count).toBe(0)
    expect(counter.doubleCount).toBe(0)
  })

  it('increments count correctly', () => {
    const counter = useCounterStore()
    
    counter.increment()
    expect(counter.count).toBe(1)
    expect(counter.doubleCount).toBe(2)
    
    counter.increment()
    expect(counter.count).toBe(2)
    expect(counter.doubleCount).toBe(4)
  })

  it('doubleCount getter works correctly', () => {
    const counter = useCounterStore()
    
    expect(counter.doubleCount).toBe(0)
    
    counter.count = 3
    expect(counter.doubleCount).toBe(6)
    
    counter.count = 7
    expect(counter.doubleCount).toBe(14)
  })

  it('actions can be called multiple times', () => {
    const counter = useCounterStore()
    
    for (let i = 0; i < 10; i++) {
      counter.increment()
    }
    expect(counter.count).toBe(10)
    expect(counter.doubleCount).toBe(20)
  })

  it('state can be manually reset', () => {
    const counter = useCounterStore()
    
    counter.count = 15
    expect(counter.count).toBe(15)
    expect(counter.doubleCount).toBe(30)
    
    // Manual reset
    counter.count = 0
    expect(counter.count).toBe(0)
    expect(counter.doubleCount).toBe(0)
  })
})