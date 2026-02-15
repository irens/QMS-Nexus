// 响应式适配优化
import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 响应式断点
 */
export const BREAKPOINTS = {
  MOBILE: 768,    // 手机端
  TABLET: 1024,   // 平板端
  DESKTOP: 1280,  // 桌面端
  LARGE: 1440     // 大屏端
} as const

/**
 * 设备类型
 */
export type DeviceType = 'mobile' | 'tablet' | 'desktop' | 'large'

/**
 * 响应式工具类
 */
export class ResponsiveUtil {
  private static instance: ResponsiveUtil
  private deviceType = ref<DeviceType>('desktop')
  private isMobile = ref(false)
  private isTablet = ref(false)
  private isDesktop = ref(false)
  private isLarge = ref(false)
  
  private constructor() {
    this.updateDeviceType()
    this.setupEventListeners()
  }

  /**
   * 获取单例实例
   */
  static getInstance(): ResponsiveUtil {
    if (!ResponsiveUtil.instance) {
      ResponsiveUtil.instance = new ResponsiveUtil()
    }
    return ResponsiveUtil.instance
  }

  /**
   * 更新设备类型
   */
  private updateDeviceType(): void {
    const width = window.innerWidth
    
    if (width < BREAKPOINTS.MOBILE) {
      this.deviceType.value = 'mobile'
      this.isMobile.value = true
      this.isTablet.value = false
      this.isDesktop.value = false
      this.isLarge.value = false
    } else if (width < BREAKPOINTS.TABLET) {
      this.deviceType.value = 'tablet'
      this.isMobile.value = false
      this.isTablet.value = true
      this.isDesktop.value = false
      this.isLarge.value = false
    } else if (width < BREAKPOINTS.DESKTOP) {
      this.deviceType.value = 'desktop'
      this.isMobile.value = false
      this.isTablet.value = false
      this.isDesktop.value = true
      this.isLarge.value = false
    } else {
      this.deviceType.value = 'large'
      this.isMobile.value = false
      this.isTablet.value = false
      this.isDesktop.value = true
      this.isLarge.value = true
    }
  }

  /**
   * 设置事件监听器
   */
  private setupEventListeners(): void {
    const handleResize = () => {
      this.updateDeviceType()
    }

    // 使用防抖优化性能
    let resizeTimer: number | null = null
    const debouncedResize = () => {
      if (resizeTimer) {
        clearTimeout(resizeTimer)
      }
      resizeTimer = window.setTimeout(handleResize, 100)
    }

    window.addEventListener('resize', debouncedResize)
    
    // 清理函数
    return () => {
      window.removeEventListener('resize', debouncedResize)
      if (resizeTimer) {
        clearTimeout(resizeTimer)
      }
    }
  }

  /**
   * 获取当前设备类型
   */
  getDeviceType(): DeviceType {
    return this.deviceType.value
  }

  /**
   * 是否移动端
   */
  isMobileDevice(): boolean {
    return this.isMobile.value
  }

  /**
   * 是否平板端
   */
  isTabletDevice(): boolean {
    return this.isTablet.value
  }

  /**
   * 是否桌面端
   */
  isDesktopDevice(): boolean {
    return this.isDesktop.value
  }

  /**
   * 是否大屏端
   */
  isLargeDevice(): boolean {
    return this.isLarge.value
  }

  /**
   * 获取当前断点
   */
  getCurrentBreakpoint(): number {
    return window.innerWidth
  }

  /**
   * 根据设备类型返回不同的值
   */
  responsiveValue<T>(mobile: T, tablet: T, desktop: T, large?: T): T {
    if (this.isMobile.value) return mobile
    if (this.isTablet.value) return tablet
    if (this.isLarge.value && large !== undefined) return large
    return desktop
  }

  /**
   * 根据设备类型执行不同的函数
   */
  responsiveAction<T>(
    mobile: () => T,
    tablet: () => T,
    desktop: () => T,
    large?: () => T
  ): T {
    if (this.isMobile.value) return mobile()
    if (this.isTablet.value) return tablet()
    if (this.isLarge.value && large) return large()
    return desktop()
  }
}

/**
 * 响应式工具组合式函数
 */
export function useResponsive() {
  const responsiveUtil = ResponsiveUtil.getInstance()
  
  return {
    deviceType: responsiveUtil.getDeviceType(),
    isMobile: responsiveUtil.isMobileDevice(),
    isTablet: responsiveUtil.isTabletDevice(),
    isDesktop: responsiveUtil.isDesktopDevice(),
    isLarge: responsiveUtil.isLargeDevice(),
    responsiveValue: responsiveUtil.responsiveValue.bind(responsiveUtil),
    responsiveAction: responsiveUtil.responsiveAction.bind(responsiveUtil)
  }
}

/**
 * 响应式组件配置
 */
export const RESPONSIVE_CONFIG = {
  // Element Plus 组件响应式配置
  table: {
    mobile: {
      size: 'small',
      stripe: true,
      border: false
    },
    tablet: {
      size: 'default',
      stripe: true,
      border: true
    },
    desktop: {
      size: 'default',
      stripe: true,
      border: true
    }
  },
  
  form: {
    mobile: {
      labelWidth: '80px',
      size: 'small'
    },
    tablet: {
      labelWidth: '100px',
      size: 'default'
    },
    desktop: {
      labelWidth: '120px',
      size: 'default'
    }
  },
  
  button: {
    mobile: {
      size: 'small',
      round: true
    },
    tablet: {
      size: 'default',
      round: false
    },
    desktop: {
      size: 'default',
      round: false
    }
  },
  
  input: {
    mobile: {
      size: 'small'
    },
    tablet: {
      size: 'default'
    },
    desktop: {
      size: 'default'
    }
  }
} as const

/**
 * 获取响应式配置
 */
export function getResponsiveConfig<T extends keyof typeof RESPONSIVE_CONFIG>(
  component: T,
  deviceType: DeviceType
): (typeof RESPONSIVE_CONFIG)[T][DeviceType] {
  return RESPONSIVE_CONFIG[component][deviceType]
}

/**
 * 响应式网格布局
 */
export const RESPONSIVE_GRID = {
  // 列数配置
  columns: {
    mobile: 1,
    tablet: 2,
    desktop: 3,
    large: 4
  },
  
  // 间距配置
  gap: {
    mobile: '16px',
    tablet: '20px',
    desktop: '24px',
    large: '32px'
  },
  
  // 卡片间距
  cardGap: {
    mobile: '12px',
    tablet: '16px',
    desktop: '20px',
    large: '24px'
  }
} as const

/**
 * 响应式字体大小
 */
export const RESPONSIVE_FONT_SIZE = {
  title: {
    mobile: 'text-lg',
    tablet: 'text-xl',
    desktop: 'text-2xl',
    large: 'text-3xl'
  },
  subtitle: {
    mobile: 'text-base',
    tablet: 'text-lg',
    desktop: 'text-xl',
    large: 'text-2xl'
  },
  body: {
    mobile: 'text-sm',
    tablet: 'text-base',
    desktop: 'text-base',
    large: 'text-lg'
  },
  small: {
    mobile: 'text-xs',
    tablet: 'text-sm',
    desktop: 'text-sm',
    large: 'text-sm'
  }
} as const

/**
 * 响应式工具类生成器
 */
export function generateResponsiveClasses(deviceType: DeviceType): string[] {
  const classes: string[] = []
  
  // 基础响应式类
  classes.push(`device-${deviceType}`)
  
  // 字体大小类
  Object.entries(RESPONSIVE_FONT_SIZE).forEach(([key, sizes]) => {
    classes.push(`${key}-${sizes[deviceType].replace('text-', '')}`)
  })
  
  // 网格布局类
  classes.push(`grid-cols-${RESPONSIVE_GRID.columns[deviceType]}`)
  classes.push(`gap-${RESPONSIVE_GRID.gap[deviceType].replace('px', '')}`)
  
  return classes
}

/**
 * 触摸事件支持
 */
export function useTouchEvents() {
  const isTouch = ref('ontouchstart' in window)
  const touchStartX = ref(0)
  const touchStartY = ref(0)
  
  const onTouchStart = (event: TouchEvent) => {
    touchStartX.value = event.touches[0].clientX
    touchStartY.value = event.touches[0].clientY
  }
  
  const onTouchMove = (event: TouchEvent) => {
    if (!isTouch.value) return
    
    const touchEndX = event.touches[0].clientX
    const touchEndY = event.touches[0].clientY
    
    const deltaX = touchEndX - touchStartX.value
    const deltaY = touchEndY - touchStartY.value
    
    // 可以在这里处理滑动手势
    return {
      deltaX,
      deltaY,
      direction: Math.abs(deltaX) > Math.abs(deltaY) ? 'horizontal' : 'vertical'
    }
  }
  
  return {
    isTouch,
    onTouchStart,
    onTouchMove
  }
}