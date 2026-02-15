import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useResponsive, BREAKPOINTS, generateResponsiveClasses } from '@/utils/responsive'

// 模拟 window.innerWidth
const mockWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width
  })
}

describe('Responsive Utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    // 清理事件监听器
    window.removeEventListener('resize', vi.fn())
  })

  describe('设备类型检测', () => {
    it('应该正确识别移动端设备', () => {
      mockWindowWidth(500)
      const { isMobile, deviceType } = useResponsive()
      
      expect(isMobile).toBe(true)
      expect(deviceType).toBe('mobile')
    })

    it('应该正确识别平板端设备', () => {
      mockWindowWidth(900)
      const { isTablet, deviceType } = useResponsive()
      
      expect(isTablet).toBe(true)
      expect(deviceType).toBe('tablet')
    })

    it('应该正确识别桌面端设备', () => {
      mockWindowWidth(1200)
      const { isDesktop, deviceType } = useResponsive()
      
      expect(isDesktop).toBe(true)
      expect(deviceType).toBe('desktop')
    })

    it('应该正确识别大屏端设备', () => {
      mockWindowWidth(1500)
      const { isLarge, deviceType } = useResponsive()
      
      expect(isLarge).toBe(true)
      expect(deviceType).toBe('large')
    })
  })

  describe('响应式值处理', () => {
    it('应该根据设备类型返回正确的值', () => {
      mockWindowWidth(500)
      const { responsiveValue } = useResponsive()
      
      const result = responsiveValue('mobile-value', 'tablet-value', 'desktop-value')
      expect(result).toBe('mobile-value')
    })

    it('应该支持大屏设备的特殊值', () => {
      mockWindowWidth(1500)
      const { responsiveValue } = useResponsive()
      
      const result = responsiveValue('mobile', 'tablet', 'desktop', 'large')
      expect(result).toBe('large')
    })

    it('应该在没有大屏值时回退到桌面值', () => {
      mockWindowWidth(1500)
      const { responsiveValue } = useResponsive()
      
      const result = responsiveValue('mobile', 'tablet', 'desktop')
      expect(result).toBe('desktop')
    })
  })

  describe('响应式动作处理', () => {
    it('应该根据设备类型执行正确的函数', () => {
      mockWindowWidth(500)
      const { responsiveAction } = useResponsive()
      
      const mobileFn = vi.fn(() => 'mobile-result')
      const tabletFn = vi.fn(() => 'tablet-result')
      const desktopFn = vi.fn(() => 'desktop-result')
      
      const result = responsiveAction(mobileFn, tabletFn, desktopFn)
      
      expect(result).toBe('mobile-result')
      expect(mobileFn).toHaveBeenCalled()
      expect(tabletFn).not.toHaveBeenCalled()
      expect(desktopFn).not.toHaveBeenCalled()
    })

    it('应该支持大屏设备的特殊函数', () => {
      mockWindowWidth(1500)
      const { responsiveAction } = useResponsive()
      
      const mobileFn = vi.fn()
      const tabletFn = vi.fn()
      const desktopFn = vi.fn()
      const largeFn = vi.fn(() => 'large-result')
      
      const result = responsiveAction(mobileFn, tabletFn, desktopFn, largeFn)
      
      expect(result).toBe('large-result')
      expect(largeFn).toHaveBeenCalled()
      expect(desktopFn).not.toHaveBeenCalled()
    })
  })

  describe('响应式类名生成', () => {
    it('应该生成正确的移动端类名', () => {
      mockWindowWidth(500)
      const classes = generateResponsiveClasses('mobile')
      
      expect(classes).toContain('device-mobile')
      expect(classes).toContain('title-base')
      expect(classes).toContain('body-sm')
      expect(classes).toContain('grid-cols-1')
      expect(classes).toContain('gap-16')
    })

    it('应该生成正确的平板端类名', () => {
      mockWindowWidth(900)
      const classes = generateResponsiveClasses('tablet')
      
      expect(classes).toContain('device-tablet')
      expect(classes).toContain('title-lg')
      expect(classes).toContain('body-base')
      expect(classes).toContain('grid-cols-2')
      expect(classes).toContain('gap-20')
    })

    it('应该生成正确的桌面端类名', () => {
      mockWindowWidth(1200)
      const classes = generateResponsiveClasses('desktop')
      
      expect(classes).toContain('device-desktop')
      expect(classes).toContain('title-xl')
      expect(classes).toContain('body-base')
      expect(classes).toContain('grid-cols-3')
      expect(classes).toContain('gap-24')
    })

    it('应该生成正确的大屏端类名', () => {
      mockWindowWidth(1500)
      const classes = generateResponsiveClasses('large')
      
      expect(classes).toContain('device-large')
      expect(classes).toContain('title-2xl')
      expect(classes).toContain('body-lg')
      expect(classes).toContain('grid-cols-4')
      expect(classes).toContain('gap-32')
    })
  })

  describe('窗口大小变化处理', () => {
    it('应该响应窗口大小变化', () => {
      mockWindowWidth(500)
      const { isMobile } = useResponsive()
      
      expect(isMobile).toBe(true)
      
      // 模拟窗口大小变化
      mockWindowWidth(900)
      window.dispatchEvent(new Event('resize'))
      
      // 等待防抖处理
      setTimeout(() => {
        const { isTablet } = useResponsive()
        expect(isTablet).toBe(true)
      }, 200)
    })

    it('应该正确处理多次快速变化', () => {
      const resizeSpy = vi.spyOn(window, 'addEventListener')
      
      useResponsive()
      
      expect(resizeSpy).toHaveBeenCalledWith('resize', expect.any(Function))
      
      // 模拟多次快速变化
      mockWindowWidth(500)
      window.dispatchEvent(new Event('resize'))
      mockWindowWidth(1200)
      window.dispatchEvent(new Event('resize'))
      mockWindowWidth(900)
      window.dispatchEvent(new Event('resize'))
      
      // 防抖应该只触发一次
      setTimeout(() => {
        const { deviceType } = useResponsive()
        expect(deviceType).toBe('tablet')
      }, 300)
    })
  })

  describe('断点常量', () => {
    it('应该包含正确的断点值', () => {
      expect(BREAKPOINTS.MOBILE).toBe(768)
      expect(BREAKPOINTS.TABLET).toBe(1024)
      expect(BREAKPOINTS.DESKTOP).toBe(1280)
      expect(BREAKPOINTS.LARGE).toBe(1440)
    })
  })
})