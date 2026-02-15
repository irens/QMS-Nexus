import { describe, it, expect } from 'vitest'
import {
  validateEmail,
  validatePhone,
  validateIP,
  validatePasswordStrength,
  validateFilename,
  validateTagName,
  createValidator,
  validationRules
} from '../validation'

describe('Validation Utils', () => {
  describe('validateEmail', () => {
    it('returns true for valid email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true)
      expect(validateEmail('user.name@domain.co.uk')).toBe(true)
      expect(validateEmail('test+tag@example.org')).toBe(true)
    })

    it('returns false for invalid email addresses', () => {
      expect(validateEmail('invalid-email')).toBe(false)
      expect(validateEmail('test@')).toBe(false)
      expect(validateEmail('@example.com')).toBe(false)
      expect(validateEmail('test@.com')).toBe(false)
      expect(validateEmail('')).toBe(false)
    })
  })

  describe('validatePhone', () => {
    it('returns true for valid phone numbers', () => {
      expect(validatePhone('13800138000')).toBe(true)
      expect(validatePhone('14700147000')).toBe(true)
      expect(validatePhone('19900199000')).toBe(true)
    })

    it('returns false for invalid phone numbers', () => {
      expect(validatePhone('12345678901')).toBe(false)
      expect(validatePhone('1380013800')).toBe(false)
      expect(validatePhone('138001380000')).toBe(false)
      expect(validatePhone('abc13800138000')).toBe(false)
      expect(validatePhone('')).toBe(false)
    })
  })

  describe('validateIP', () => {
    it('returns true for valid IP addresses', () => {
      expect(validateIP('192.168.1.1')).toBe(true)
      expect(validateIP('10.0.0.1')).toBe(true)
      expect(validateIP('172.16.0.1')).toBe(true)
      expect(validateIP('8.8.8.8')).toBe(true)
    })

    it('returns false for invalid IP addresses', () => {
      expect(validateIP('192.168.1')).toBe(false)
      expect(validateIP('192.168.1.1.1')).toBe(false)
      expect(validateIP('256.168.1.1')).toBe(false)
      expect(validateIP('192.168.1.256')).toBe(false)
      expect(validateIP('abc.def.ghi.jkl')).toBe(false)
      expect(validateIP('')).toBe(false)
    })
  })

  describe('validatePasswordStrength', () => {
    it('returns weak for simple passwords', () => {
      expect(validatePasswordStrength('password')).toBe('weak')
      expect(validatePasswordStrength('123456')).toBe('weak')
      expect(validatePasswordStrength('abc')).toBe('weak')
    })

    it('returns medium for moderate passwords', () => {
      expect(validatePasswordStrength('Password123')).toBe('medium')
      expect(validatePasswordStrength('Test2024')).toBe('medium')
      expect(validatePasswordStrength('A1b2C3d4')).toBe('medium')
    })

    it('returns strong for complex passwords', () => {
      expect(validatePasswordStrength('Password123!')).toBe('strong')
      expect(validatePasswordStrength('Test@2024')).toBe('strong')
      expect(validatePasswordStrength('A1b2C3d4!')).toBe('strong')
    })
  })

  describe('validateFilename', () => {
    it('returns true for valid filenames', () => {
      expect(validateFilename('document.pdf')).toBe(true)
      expect(validateFilename('my-file_2024.docx')).toBe(true)
      expect(validateFilename('test file.txt')).toBe(true)
    })

    it('returns false for invalid filenames', () => {
      expect(validateFilename('')).toBe(false)
      expect(validateFilename('file/with/slashes.txt')).toBe(false)
      expect(validateFilename('file:with:colons.txt')).toBe(false)
      expect(validateFilename('file*with*asterisks.txt')).toBe(false)
      expect(validateFilename('file?with?questions.txt')).toBe(false)
    })

    it('handles edge cases correctly', () => {
      expect(validateFilename('a')).toBe(true)
      expect(validateFilename('file with spaces.txt')).toBe(true)
      expect(validateFilename('file_with_underscores.txt')).toBe(true)
      expect(validateFilename('file-with-dashes.txt')).toBe(true)
      expect(validateFilename('.txt')).toBe(true) // Starting with dot is valid
    })
  })

  describe('validateTagName', () => {
    it('returns true for valid tag names', () => {
      expect(validateTagName('important')).toBe(true)
      expect(validateTagName('work-document')).toBe(true)
      expect(validateTagName('2024')).toBe(true)
      expect(validateTagName('tag_with_underscore')).toBe(true)
    })

    it('returns false for invalid tag names', () => {
      expect(validateTagName('')).toBe(false)
      expect(validateTagName('tag with spaces')).toBe(false)
      expect(validateTagName('tag@with@special')).toBe(false)
      expect(validateTagName('tag#with#hash')).toBe(false)
      expect(validateTagName('verylongtagnamethatexceedsthemaximumallowedlength')).toBe(false)
    })

    it('handles special characters correctly', () => {
      expect(validateTagName('中文标签')).toBe(true)
      expect(validateTagName('tag-with-dash')).toBe(true)
      expect(validateTagName('tag_with_underscore')).toBe(true)
      expect(validateTagName('tag.with.dot')).toBe(false)
    })
  })

  describe('validationRules', () => {
    it('required rule works correctly', () => {
      const required = validationRules.required()
      expect(required('content')).toBe(true)
      expect(required('')).toBe('此字段为必填项')
      expect(required(null)).toBe('此字段为必填项')
      expect(required(undefined)).toBe('此字段为必填项')
    })

    it('email rule works correctly', () => {
      const email = validationRules.email()
      expect(email('test@example.com')).toBe(true)
      expect(email('invalid-email')).toBe('请输入有效的邮箱地址')
      expect(email('')).toBe('请输入有效的邮箱地址')
    })

    it('phone rule works correctly', () => {
      const phone = validationRules.phone()
      expect(phone('13800138000')).toBe(true)
      expect(phone('12345678901')).toBe('请输入有效的手机号')
      expect(phone('')).toBe('请输入有效的手机号')
    })

    it('accepts custom error messages', () => {
      const required = validationRules.required('This field is required')
      expect(required('')).toBe('This field is required')
      
      const email = validationRules.email('Invalid email format')
      expect(email('invalid')).toBe('Invalid email format')
    })
  })
})