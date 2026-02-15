import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IconTooling from '../IconTooling.vue'

describe('IconTooling', () => {
  it('renders SVG icon', () => {
    const wrapper = mount(IconTooling)
    
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('has correct SVG attributes', () => {
    const wrapper = mount(IconTooling)
    
    const svg = wrapper.find('svg')
    expect(svg.attributes('xmlns')).toBe('http://www.w3.org/2000/svg')
    expect(svg.attributes('width')).toBeDefined()
    expect(svg.attributes('height')).toBeDefined()
    expect(svg.attributes('fill')).toBe('currentColor')
  })

  it('contains path element', () => {
    const wrapper = mount(IconTooling)
    
    expect(wrapper.find('path').exists()).toBe(true)
  })

  it('renders icon element correctly', () => {
    const wrapper = mount(IconTooling)
    
    expect(wrapper.element.tagName).toBe('svg')
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})