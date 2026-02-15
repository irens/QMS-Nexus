// 验证工具函数

/**
 * 邮箱验证
 * @param email - 邮箱地址
 * @returns 是否为有效邮箱
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 手机号验证（中国大陆）
 * @param phone - 手机号
 * @returns 是否为有效手机号
 */
export function validatePhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 密码强度验证
 * @param password - 密码
 * @returns 密码强度等级：weak、medium、strong
 */
export function validatePasswordStrength(password: string): 'weak' | 'medium' | 'strong' {
  let strength = 0
  
  // 长度检查
  if (password.length >= 8) strength++
  if (password.length >= 12) strength++
  
  // 字符类型检查
  if (/[a-z]/.test(password)) strength++ // 小写字母
  if (/[A-Z]/.test(password)) strength++ // 大写字母
  if (/\d/.test(password)) strength++ // 数字
  if (/[^\w\s]/.test(password)) strength++ // 特殊字符
  
  if (strength <= 2) return 'weak'
  if (strength <= 4) return 'medium'
  return 'strong'
}

/**
 * 文件名校验
 * @param filename - 文件名
 * @returns 是否为有效文件名
 */
export function validateFilename(filename: string): boolean {
  // 不允许包含特殊字符：<>:"/\\|?*
  const invalidChars = /[<>:"\/\\|?*]/
  return !invalidChars.test(filename) && filename.length > 0 && filename.length <= 255
}

/**
 * 标签名校验
 * @param tagName - 标签名
 * @returns 是否为有效标签名
 */
export function validateTagName(tagName: string): boolean {
  // 标签名长度1-20个字符，只允许字母、数字、中文、下划线、连字符
  const tagRegex = /^[\u4e00-\u9fa5a-zA-Z0-9_-]{1,20}$/
  return tagRegex.test(tagName)
}

/**
 * IP地址验证
 * @param ip - IP地址
 * @returns 是否为有效IP地址
 */
export function validateIP(ip: string): boolean {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipRegex.test(ip)
}

/**
 * 表单验证错误信息
 */
export interface ValidationError {
  field: string
  message: string
  value?: any
}

/**
 * 通用表单验证结果
 */
export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
}

/**
 * 创建验证器
 * @param rules - 验证规则
 * @returns 验证函数
 */
export function createValidator(rules: Record<string, Array<(value: any) => string | true>>) {
  return function validate(data: Record<string, any>): ValidationResult {
    const errors: ValidationError[] = []
    
    for (const [field, fieldRules] of Object.entries(rules)) {
      const value = data[field]
      
      for (const rule of fieldRules) {
        const result = rule(value)
        if (result !== true) {
          errors.push({
            field,
            message: result as string,
            value
          })
          break // 每个字段只返回第一个错误
        }
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    }
  }
}

/**
 * 常用验证规则
 */
export const validationRules = {
  required: (message = '此字段为必填项') => (value: any) => {
    if (value === null || value === undefined || value === '') {
      return message
    }
    return true
  },
  
  email: (message = '请输入有效的邮箱地址') => (value: string) => {
    if (!validateEmail(value)) {
      return message
    }
    return true
  },
  
  phone: (message = '请输入有效的手机号') => (value: string) => {
    if (!validatePhone(value)) {
      return message
    }
    return true
  },
  
  minLength: (min: number, message?: string) => (value: string) => {
    if (value.length < min) {
      return message || `长度不能少于${min}个字符`
    }
    return true
  },
  
  maxLength: (max: number, message?: string) => (value: string) => {
    if (value.length > max) {
      return message || `长度不能超过${max}个字符`
    }
    return true
  },
  
  filename: (message = '文件名包含非法字符') => (value: string) => {
    if (!validateFilename(value)) {
      return message
    }
    return true
  },
  
  tagName: (message = '标签名只能包含字母、数字、中文、下划线、连字符') => (value: string) => {
    if (!validateTagName(value)) {
      return message
    }
    return true
  }
}