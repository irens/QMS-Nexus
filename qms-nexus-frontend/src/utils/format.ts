// 日期时间工具函数

/**
 * 格式化日期时间
 * @param date - 日期对象或时间戳
 * @param format - 格式字符串，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export function formatDateTime(date: Date | number | string, format: string = 'YYYY-MM-DD HH:mm:ss'): string {
  const d = new Date(date)
  
  // 转换为本地时间（考虑时区）
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化相对时间
 * @param date - 日期对象或时间戳
 * @returns 相对时间描述（如：刚刚、5分钟前、1小时前）
 */
export function formatRelativeTime(date: Date | number | string): string {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (seconds < 60) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 30) {
    return `${days}天前`
  } else {
    return formatDateTime(d, 'YYYY-MM-DD')
  }
}

/**
 * 格式化文件大小
 * @param bytes - 字节数
 * @returns 格式化后的文件大小（如：1.5MB、2.3GB）
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化持续时间
 * @param milliseconds - 毫秒数
 * @returns 格式化后的时间（如：1.2s、3.5min）
 */
export function formatDuration(milliseconds: number): string {
  if (milliseconds < 1000) {
    return `${milliseconds}ms`
  } else if (milliseconds < 60000) {
    return `${(milliseconds / 1000).toFixed(1)}s`
  } else {
    return `${(milliseconds / 60000).toFixed(1)}min`
  }
}

/**
 * 格式化日期（简化版）
 * @param date - 日期对象、时间戳或字符串
 * @param fallback - 当日期无效时的回退文本
 * @returns 格式化后的日期字符串或回退文本
 */
export function formatDate(date: Date | number | string | undefined | null, fallback: string = '未知'): string {
  if (!date) return fallback
  
  try {
    const d = new Date(date)
    if (isNaN(d.getTime())) return fallback
    
    return d.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return fallback
  }
}