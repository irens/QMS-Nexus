import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TheWelcome from '../TheWelcome.vue'

describe('TheWelcome', () => {
  it('renders welcome section', () => {
    const wrapper = mount(TheWelcome)
    
    expect(wrapper.element.tagName).toBe('DIV')
  })

  it('contains welcome title', () => {
    const wrapper = mount(TheWelcome)
    
    const title = wrapper.find('h2')
    expect(title.exists()).toBe(true)
    expect(title.text()).toContain('Welcome')
  })

  it('renders welcome items', () => {
    const wrapper = mount(TheWelcome)
    
    const welcomeItems = wrapper.findAllComponents({ name: 'WelcomeItem' })
    expect(welcomeItems.length).toBeGreaterThan(0)
  })

  it('has proper element structure', () => {
    const wrapper = mount(TheWelcome)
    
    expect(wrapper.element.tagName).toBe('DIV')
    expect(wrapper.find('h2').exists()).toBe(true)
  })
})