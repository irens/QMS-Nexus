import { describe, it, expect } from 'vitest'
import { 
  getFileExtension, 
  getFileIcon, 
  getFileColor,
  validateFileType,
  validateFileSize,
  fileToBase64,
  downloadFile,
  getFileHash
} from '../file'

describe('File Utils', () => {
  describe('getFileExtension', () => {
    it('returns correct extension for valid filenames', () => {
      expect(getFileExtension('test.pdf')).toBe('pdf')
      expect(getFileExtension('document.docx')).toBe('docx')
      expect(getFileExtension('image.png')).toBe('png')
      expect(getFileExtension('archive.tar.gz')).toBe('gz')
    })

    it('returns empty string for filenames without extension', () => {
      expect(getFileExtension('README')).toBe('')
      expect(getFileExtension('')).toBe('')
    })

    it('handles edge cases correctly', () => {
      expect(getFileExtension('.gitignore')).toBe('gitignore')
      expect(getFileExtension('file.')).toBe('')
    })
  })

  describe('getFileIcon', () => {
    it('returns correct icon for document types', () => {
      expect(getFileIcon('test.pdf')).toBe('file-pdf')
      expect(getFileIcon('document.doc')).toBe('file-word')
      expect(getFileIcon('document.docx')).toBe('file-word')
    })

    it('returns correct icon for image types', () => {
      expect(getFileIcon('image.png')).toBe('file-image')
      expect(getFileIcon('image.jpg')).toBe('file-image')
      expect(getFileIcon('image.jpeg')).toBe('file-image')
    })

    it('returns default icon for unknown types', () => {
      expect(getFileIcon('unknown')).toBe('file-unknown')
      expect(getFileIcon('')).toBe('file-unknown')
    })
  })

  describe('getFileColor', () => {
    it('returns correct color for document types', () => {
      expect(getFileColor('test.pdf')).toBe('#dc2626')
      expect(getFileColor('document.doc')).toBe('#2563eb')
      expect(getFileColor('document.docx')).toBe('#2563eb')
    })

    it('returns correct color for image types', () => {
      expect(getFileColor('image.png')).toBe('#9333ea')
      expect(getFileColor('image.jpg')).toBe('#9333ea')
    })

    it('returns default color for unknown types', () => {
      expect(getFileColor('unknown')).toBe('#6b7280')
      expect(getFileColor('')).toBe('#6b7280')
    })
  })

  describe('validateFileType', () => {
    it('returns true for valid file types', () => {
      const validTypes = ['.pdf', '.doc', '.docx', '.png', '.jpg']
      const pdfFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      const pngFile = new File(['content'], 'image.png', { type: 'image/png' })
      
      expect(validateFileType(pdfFile, validTypes)).toBe(true)
      expect(validateFileType(pngFile, validTypes)).toBe(true)
    })

    it('returns false for invalid file types', () => {
      const validTypes = ['.pdf', '.doc', '.docx']
      const txtFile = new File(['content'], 'test.txt', { type: 'text/plain' })
      const jsFile = new File(['content'], 'script.js', { type: 'application/javascript' })
      
      expect(validateFileType(txtFile, validTypes)).toBe(false)
      expect(validateFileType(jsFile, validTypes)).toBe(false)
    })

    it('handles MIME type validation', () => {
      const validTypes = ['application/pdf', 'image/png']
      const pdfFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      const pngFile = new File(['content'], 'image.png', { type: 'image/png' })
      
      expect(validateFileType(pdfFile, validTypes)).toBe(true)
      expect(validateFileType(pngFile, validTypes)).toBe(true)
    })
  })

  describe('validateFileSize', () => {
    it('returns true for files within size limit', () => {
      const smallFile = new File(['content'], 'test.txt', { type: 'text/plain' })
      Object.defineProperty(smallFile, 'size', { value: 1024 }) // 1KB
      
      expect(validateFileSize(smallFile, 2 * 1024 * 1024)).toBe(true) // 2MB limit
    })

    it('returns false for files exceeding size limit', () => {
      const largeFile = new File(['content'], 'test.txt', { type: 'text/plain' })
      Object.defineProperty(largeFile, 'size', { value: 3 * 1024 * 1024 }) // 3MB
      
      expect(validateFileSize(largeFile, 2 * 1024 * 1024)).toBe(false) // 2MB limit
    })

    it('handles edge cases correctly', () => {
      const emptyFile = new File([''], 'empty.txt', { type: 'text/plain' })
      Object.defineProperty(emptyFile, 'size', { value: 0 })
      
      expect(validateFileSize(emptyFile, 1024 * 1024)).toBe(true) // 0 bytes is valid
    })
  })

  describe('fileToBase64', () => {
    it('converts file to base64 string', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
      const base64 = await fileToBase64(mockFile)
      
      expect(typeof base64).toBe('string')
      expect(base64.length).toBeGreaterThan(0)
    })

    it('handles empty file', async () => {
      const emptyFile = new File([], 'empty.txt', { type: 'text/plain' })
      const base64 = await fileToBase64(emptyFile)
      
      expect(typeof base64).toBe('string')
    })
  })

  describe('getFileHash', () => {
    it('generates consistent hash for same content', async () => {
      // Mock File.arrayBuffer method
      const mockArrayBuffer = new ArrayBuffer(8)
      const file1 = new File(['test content'], 'test1.txt', { type: 'text/plain' })
      const file2 = new File(['test content'], 'test2.txt', { type: 'text/plain' })
      
      // Mock arrayBuffer method
      Object.defineProperty(file1, 'arrayBuffer', {
        value: () => Promise.resolve(mockArrayBuffer)
      })
      Object.defineProperty(file2, 'arrayBuffer', {
        value: () => Promise.resolve(mockArrayBuffer)
      })
      
      const hash1 = await getFileHash(file1)
      const hash2 = await getFileHash(file2)
      
      expect(hash1).toBe(hash2)
      expect(typeof hash1).toBe('string')
      expect(hash1.length).toBeGreaterThan(0) // 哈希长度应该大于0
    })

    it('generates different hash for different content', async () => {
      const mockArrayBuffer1 = new ArrayBuffer(8)
      const mockArrayBuffer2 = new ArrayBuffer(16)
      
      const file1 = new File(['content 1'], 'test1.txt', { type: 'text/plain' })
      const file2 = new File(['content 2'], 'test2.txt', { type: 'text/plain' })
      
      Object.defineProperty(file1, 'arrayBuffer', {
        value: () => Promise.resolve(mockArrayBuffer1)
      })
      Object.defineProperty(file2, 'arrayBuffer', {
        value: () => Promise.resolve(mockArrayBuffer2)
      })
      
      const hash1 = await getFileHash(file1)
      const hash2 = await getFileHash(file2)
      
      expect(hash1).not.toBe(hash2)
    })
  })
})