import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IconSupport from '../IconSupport.vue'

describe('IconSupport', () => {
  it('renders SVG icon', () => {
    const wrapper = mount(IconSupport)
    
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('has correct SVG attributes', () => {
    const wrapper = mount(IconSupport)
    
    const svg = wrapper.find('svg')
    expect(svg.attributes('xmlns')).toBe('http://www.w3.org/2000/svg')
    expect(svg.attributes('width')).toBeDefined()
    expect(svg.attributes('height')).toBeDefined()
    expect(svg.attributes('fill')).toBe('currentColor')
  })

  it('contains path element', () => {
    const wrapper = mount(IconSupport)
    
    expect(wrapper.find('path').exists()).toBe(true)
  })

  it('renders icon element correctly', () => {
    const wrapper = mount(IconSupport)
    
    expect(wrapper.element.tagName).toBe('svg')
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})