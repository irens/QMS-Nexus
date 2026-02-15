import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IconDocumentation from '../IconDocumentation.vue'

describe('IconDocumentation', () => {
  it('renders SVG icon', () => {
    const wrapper = mount(IconDocumentation)
    
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('has correct SVG attributes', () => {
    const wrapper = mount(IconDocumentation)
    
    const svg = wrapper.find('svg')
    expect(svg.attributes('xmlns')).toBe('http://www.w3.org/2000/svg')
    expect(svg.attributes('width')).toBeDefined()
    expect(svg.attributes('height')).toBeDefined()
    expect(svg.attributes('fill')).toBe('currentColor')
  })

  it('contains path element', () => {
    const wrapper = mount(IconDocumentation)
    
    expect(wrapper.find('path').exists()).toBe(true)
  })

  it('renders icon element correctly', () => {
    const wrapper = mount(IconDocumentation)
    
    expect(wrapper.element.tagName).toBe('svg')
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})