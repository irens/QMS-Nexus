import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HelloWorld from '../HelloWorld.vue'

describe('HelloWorld', () => {
  it('renders properly with msg prop', () => {
    const testMsg = 'Hello Vitest'
    const wrapper = mount(HelloWorld, { props: { msg: testMsg } })
    
    expect(wrapper.text()).toContain(testMsg)
  })

  it('has correct heading structure', () => {
    const wrapper = mount(HelloWorld, { props: { msg: 'Test Message' } })
    
    const h1 = wrapper.find('h1')
    expect(h1.exists()).toBe(true)
    expect(h1.text()).toBe('Test Message')
  })

  it('contains documentation links', () => {
    const wrapper = mount(HelloWorld, { props: { msg: 'Test' } })
    
    const links = wrapper.findAll('a')
    expect(links.length).toBeGreaterThan(0)
    
    // 检查是否包含文档链接
    const hasDocumentationLinks = links.some(link => 
      link.attributes('href')?.includes('vitejs.dev') ||
      link.attributes('href')?.includes('vuejs.org') ||
      link.attributes('href')?.includes('typescriptlang.org')
    )
    expect(hasDocumentationLinks).toBe(true)
  })
})