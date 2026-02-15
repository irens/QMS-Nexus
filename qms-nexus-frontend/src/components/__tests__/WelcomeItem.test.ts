import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WelcomeItem from '../WelcomeItem.vue'

describe('WelcomeItem', () => {
  it('renders slot content', () => {
    const wrapper = mount(WelcomeItem, {
      slots: {
        default: '<div class="test-content">Test Content</div>',
        icon: '<div class="test-icon">Icon</div>'
      }
    })
    
    expect(wrapper.find('.test-content').exists()).toBe(true)
    expect(wrapper.find('.test-content').text()).toBe('Test Content')
    expect(wrapper.find('.test-icon').exists()).toBe(true)
  })

  it('has correct element structure', () => {
    const wrapper = mount(WelcomeItem, {
      slots: {
        default: '<div>Content</div>',
        icon: '<div>Icon</div>'
      }
    })
    
    expect(wrapper.element.tagName).toBe('DIV')
    expect(wrapper.classes()).toContain('item')
  })

  it('applies correct CSS classes', () => {
    const wrapper = mount(WelcomeItem, {
      slots: {
        default: '<div>Content</div>',
        icon: '<div>Icon</div>'
      }
    })
    
    expect(wrapper.classes()).toContain('item')
  })
})