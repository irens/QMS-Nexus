import { describe, it, expect } from 'vitest'
import {
  formatDateTime,
  formatRelativeTime,
  formatFileSize,
  formatDuration,
  formatDate
} from '../format'

describe('Format Utils', () => {
  describe('formatDateTime', () => {
    it('formats date correctly', () => {
      const date = new Date('2024-01-15T14:30:00')
      const result = formatDateTime(date)
      
      expect(result).toMatch(/2024-01-15/)
      expect(result).toMatch(/14:30:00/)
    })

    it('formats with custom format', () => {
      const date = new Date('2024-01-15T14:30:00')
      const result = formatDateTime(date, 'YYYY/MM/DD HH:mm')
      
      expect(result).toBe('2024/01/15 14:30')
    })

    it('handles timestamp input', () => {
      const timestamp = 1705329000000 // 2024-01-15T14:30:00
      const result = formatDateTime(timestamp)
      
      expect(result).toMatch(/2024-01-15/)
      expect(result).toMatch(/22:30:00/) // UTC+8 timezone
    })

    it('handles string date input', () => {
      const dateString = '2024-01-15T14:30:00'
      const result = formatDateTime(dateString)
      
      expect(result).toMatch(/2024-01-15/)
      expect(result).toMatch(/14:30:00/) // 使用本地时间
    })

    it('handles invalid date gracefully', () => {
      const result = formatDateTime('invalid-date')
      expect(result).toMatch(/NaN-NaN-NaN/)
    })
  })

  describe('formatRelativeTime', () => {
    const now = new Date()

    it('formats just now', () => {
      const result = formatRelativeTime(now)
      expect(result).toBe('刚刚')
    })

    it('formats minutes ago', () => {
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000)
      const result = formatRelativeTime(fiveMinutesAgo)
      expect(result).toBe('5分钟前')
    })

    it('formats hours ago', () => {
      const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000)
      const result = formatRelativeTime(twoHoursAgo)
      expect(result).toBe('2小时前')
    })

    it('formats days ago', () => {
      const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000)
      const result = formatRelativeTime(threeDaysAgo)
      expect(result).toBe('3天前')
    })

    it('handles very recent time as just now', () => {
      const future = new Date(now.getTime() + 30 * 60 * 1000)
      const result = formatRelativeTime(future)
      expect(result).toBe('刚刚') // Very recent future time
    })
  })

  describe('formatFileSize', () => {
    it('formats bytes correctly', () => {
      expect(formatFileSize(512)).toBe('512 B')
      expect(formatFileSize(1023)).toBe('1023 B')
    })

    it('formats kilobytes correctly', () => {
      expect(formatFileSize(1024)).toBe('1 KB')
      expect(formatFileSize(1536)).toBe('1.5 KB')
      expect(formatFileSize(2048)).toBe('2 KB')
    })

    it('formats megabytes correctly', () => {
      expect(formatFileSize(1024 * 1024)).toBe('1 MB')
      expect(formatFileSize(1.5 * 1024 * 1024)).toBe('1.5 MB')
      expect(formatFileSize(2 * 1024 * 1024)).toBe('2 MB')
    })

    it('formats gigabytes correctly', () => {
      expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB')
      expect(formatFileSize(2.5 * 1024 * 1024 * 1024)).toBe('2.5 GB')
    })

    it('handles zero size', () => {
      expect(formatFileSize(0)).toBe('0 B')
    })
  })

  describe('formatDuration', () => {
    it('formats milliseconds correctly', () => {
      expect(formatDuration(500)).toBe('500ms')
      expect(formatDuration(999)).toBe('999ms')
    })

    it('formats seconds correctly', () => {
      expect(formatDuration(1500)).toBe('1.5s')
      expect(formatDuration(2500)).toBe('2.5s')
      expect(formatDuration(59999)).toBe('60.0s')
    })

    it('formats minutes correctly', () => {
      expect(formatDuration(60000)).toBe('1.0min')
      expect(formatDuration(90000)).toBe('1.5min')
      expect(formatDuration(120000)).toBe('2.0min')
    })

    it('handles zero duration', () => {
      expect(formatDuration(0)).toBe('0ms')
    })

    it('handles large durations', () => {
      expect(formatDuration(3600000)).toBe('60.0min')
    })
  })

  describe('formatDate', () => {
    it('formats date correctly', () => {
      const date = new Date('2024-01-15')
      const result = formatDate(date)
      
      expect(result).toMatch(/2024/)
      expect(result).toMatch(/1/)
      expect(result).toMatch(/15/)
    })

    it('handles timestamp input', () => {
      const timestamp = 1705276800000 // 2024-01-15
      const result = formatDate(timestamp)
      
      expect(result).toMatch(/2024/)
      expect(result).toMatch(/1/)
      expect(result).toMatch(/15/)
    })

    it('handles string date input', () => {
      const dateString = '2024-01-15'
      const result = formatDate(dateString)
      
      expect(result).toMatch(/2024/)
      expect(result).toMatch(/1/)
      expect(result).toMatch(/15/)
    })

    it('returns fallback for invalid date', () => {
      expect(formatDate('invalid-date')).toBe('未知')
      expect(formatDate(null)).toBe('未知')
      expect(formatDate(undefined)).toBe('未知')
    })

    it('uses custom fallback', () => {
      expect(formatDate('invalid-date', 'N/A')).toBe('N/A')
      expect(formatDate(null, 'No date')).toBe('No date')
    })
  })
})