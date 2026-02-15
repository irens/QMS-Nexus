/**
 * 路由映射工具单元测试
 * @module utils/__tests__/route.test
 */

import { describe, it, expect } from 'vitest'
import {
  addSystemPrefix,
  removeSystemPrefix,
  hasSystemPrefix,
  getDocumentDetailRoute,
  getDocumentsRoute,
  ROUTE_PATHS
} from '../route'

describe('Route Utils', () => {
  describe('addSystemPrefix', () => {
    it('应该为路由路径添加/system前缀', () => {
      expect(addSystemPrefix('/dashboard')).toBe('/system/dashboard')
      expect(addSystemPrefix('/documents')).toBe('/system/documents')
      expect(addSystemPrefix('/documents/123')).toBe('/system/documents/123')
      expect(addSystemPrefix('/system/users')).toBe('/system/users') // 已包含前缀
    })

    it('应该处理根路径', () => {
      expect(addSystemPrefix('/')).toBe('/system/')
    })

    it('应该在路径已包含前缀时保持不变', () => {
      const path = '/system/dashboard'
      expect(addSystemPrefix(path)).toBe(path)
    })

    it('应该在路径不是以/开头时抛出错误', () => {
      expect(() => addSystemPrefix('dashboard')).toThrow('Path must start with "/"')
    })
  })

  describe('removeSystemPrefix', () => {
    it('应该移除/system前缀', () => {
      expect(removeSystemPrefix('/system/dashboard')).toBe('/dashboard')
      expect(removeSystemPrefix('/system/documents/123')).toBe('/documents/123')
    })

    it('应该在路径不包含前缀时保持不变', () => {
      expect(removeSystemPrefix('/dashboard')).toBe('/dashboard')
      expect(removeSystemPrefix('/documents')).toBe('/documents')
    })
  })

  describe('hasSystemPrefix', () => {
    it('应该在路径包含/system前缀时返回true', () => {
      expect(hasSystemPrefix('/system/dashboard')).toBe(true)
      expect(hasSystemPrefix('/system/documents/123')).toBe(true)
      expect(hasSystemPrefix('/system/')).toBe(true)
    })

    it('应该在路径不包含/system前缀时返回false', () => {
      expect(hasSystemPrefix('/dashboard')).toBe(false)
      expect(hasSystemPrefix('/documents')).toBe(false)
      expect(hasSystemPrefix('/')).toBe(false)
    })
  })

  describe('getDocumentDetailRoute', () => {
    it('应该返回正确的文档详情路由', () => {
      expect(getDocumentDetailRoute('123')).toBe('/system/documents/123')
      expect(getDocumentDetailRoute('abc-123')).toBe('/system/documents/abc-123')
    })

    it('应该处理特殊字符的文档ID', () => {
      expect(getDocumentDetailRoute('doc-123_test')).toBe('/system/documents/doc-123_test')
    })
  })

  describe('getDocumentsRoute', () => {
    it('应该返回正确的文档列表路由', () => {
      expect(getDocumentsRoute()).toBe('/system/documents')
    })
  })

  describe('ROUTE_PATHS', () => {
    it('应该包含所有基础路由', () => {
      expect(ROUTE_PATHS.DASHBOARD).toBe('/system/dashboard')
      expect(ROUTE_PATHS.UPLOAD).toBe('/system/upload')
      expect(ROUTE_PATHS.DOCUMENTS).toBe('/system/documents')
      expect(ROUTE_PATHS.TAGS).toBe('/system/tags')
      expect(ROUTE_PATHS.CHAT).toBe('/system/chat')
      expect(ROUTE_PATHS.SEARCH).toBe('/system/search')
    })

    it('应该正确生成文档详情路由', () => {
      expect(ROUTE_PATHS.DOCUMENT_DETAIL('123')).toBe('/system/documents/123')
    })

    it('应该包含系统管理路由', () => {
      expect(ROUTE_PATHS.SYSTEM_USERS).toBe('/system/system/users')
      expect(ROUTE_PATHS.SYSTEM_LOGS).toBe('/system/system/logs')
      expect(ROUTE_PATHS.SYSTEM_SETTINGS).toBe('/system/system/settings')
    })

    it('应该包含错误页面路由', () => {
      expect(ROUTE_PATHS.NOT_FOUND).toBe('/404')
    })

    it('应该包含工具函数', () => {
      expect(typeof ROUTE_PATHS.addSystemPrefix).toBe('function')
      expect(typeof ROUTE_PATHS.removeSystemPrefix).toBe('function')
      expect(typeof ROUTE_PATHS.hasSystemPrefix).toBe('function')
    })

    it('应该正确执行工具函数', () => {
      expect(ROUTE_PATHS.addSystemPrefix('/test')).toBe('/system/test')
      expect(ROUTE_PATHS.removeSystemPrefix('/system/test')).toBe('/test')
      expect(ROUTE_PATHS.hasSystemPrefix('/system/test')).toBe(true)
    })
  })

  describe('边界情况', () => {
    it('应该处理空路径', () => {
      expect(() => addSystemPrefix('')).toThrow('Path must start with "/"')
    })

    it('应该处理复杂路径', () => {
      const complexPath = '/documents/123/sections/5'
      expect(addSystemPrefix(complexPath)).toBe(`/system${complexPath}`)
    })

    it('应该处理带查询参数的路径', () => {
      expect(addSystemPrefix('/documents?page=2')).toBe('/system/documents?page=2')
    })
  })
})
