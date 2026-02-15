import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IconCommunity from '../IconCommunity.vue'

describe('IconCommunity', () => {
  it('renders SVG icon', () => {
    const wrapper = mount(IconCommunity)
    
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('has correct SVG attributes', () => {
    const wrapper = mount(IconCommunity)
    
    const svg = wrapper.find('svg')
    expect(svg.attributes('xmlns')).toBe('http://www.w3.org/2000/svg')
    expect(svg.attributes('width')).toBe('20')
    expect(svg.attributes('height')).toBe('20')
    expect(svg.attributes('fill')).toBe('currentColor')
  })

  it('contains path element', () => {
    const wrapper = mount(IconCommunity)
    
    expect(wrapper.find('path').exists()).toBe(true)
  })

  it('renders icon element correctly', () => {
    const wrapper = mount(IconCommunity)
    
    expect(wrapper.element.tagName).toBe('svg')
    expect(wrapper.find('svg').exists()).toBe(true)
  })
})