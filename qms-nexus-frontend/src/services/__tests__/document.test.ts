import { describe, it, expect, vi, beforeEach } from 'vitest'
import { documentService, DocumentService } from '../document'
import { apiClient } from '../api'

// Mock apiClient
vi.mock('../api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Document Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('DocumentService', () => {
    it('should be defined', () => {
      expect(documentService).toBeDefined()
      expect(documentService).toBeInstanceOf(DocumentService)
    })

    describe('getDocuments', () => {
      it('fetches documents list successfully', async () => {
        const mockResponse = {
          items: [
            { id: 1, name: 'Document 1', type: 'pdf' },
            { id: 2, name: 'Document 2', type: 'docx' }
          ],
          total: 2,
          page: 1,
          pageSize: 10
        }
        
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse)

        const result = await documentService.getDocuments({ page: 1, pageSize: 10 })
        
        expect(apiClient.get).toHaveBeenCalled()
        expect(result).toEqual(mockResponse)
      })

      it('fetches documents with search query', async () => {
        const mockResponse = { items: [], total: 0 }
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse)

        await documentService.getDocuments({ page: 1, pageSize: 10, search: 'test' })
        
        expect(apiClient.get).toHaveBeenCalled()
      })

      it('fetches documents with file type filter', async () => {
        const mockResponse = { items: [], total: 0 }
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse)

        await documentService.getDocuments({ 
          page: 1, 
          pageSize: 10, 
          fileType: ['pdf', 'docx'],
          tags: ['important'],
          status: ['active']
        })
        
        expect(apiClient.get).toHaveBeenCalled()
      })
    })

    describe('getDocumentById', () => {
      it('fetches single document by id', async () => {
        const mockDocument = { 
          id: 1, 
          name: 'Test Document', 
          type: 'pdf',
          size: 1024,
          uploadTime: '2024-01-15T10:00:00Z'
        }
        
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockDocument)

        const result = await documentService.getDocument('1')
        
        expect(apiClient.get).toHaveBeenCalledWith('/documents/1')
        expect(result).toEqual(mockDocument)
      })
    })

    describe('createDocument', () => {
      it('creates new document successfully', async () => {
        const newDocument = { 
          name: 'New Document', 
          type: 'pdf',
          file: 'base64content'
        }
        const mockResponse = { 
          id: 3, 
          ...newDocument,
          uploadTime: '2024-01-15T10:00:00Z'
        }
        
        vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

        const result = await documentService.createDocument(newDocument as any)
        
        expect(apiClient.post).toHaveBeenCalled()
        expect(result).toEqual(mockResponse)
      })
    })

    describe('updateDocument', () => {
      it('updates existing document', async () => {
        const updateData = { name: 'Updated Document Name' }
        const mockResponse = { 
          id: 1, 
          ...updateData,
          type: 'pdf',
          uploadTime: '2024-01-15T10:00:00Z'
        }
        
        vi.mocked(apiClient.put).mockResolvedValueOnce(mockResponse)

        const result = await documentService.updateDocumentTags('1', [updateData.name])
        
        expect(apiClient.put).toHaveBeenCalledWith('/documents/1/tags', { tags: [updateData.name] })
        expect(result).toEqual(mockResponse)
      })
    })

    describe('deleteDocument', () => {
      it('deletes document successfully', async () => {
        const mockResponse = { success: true }
        vi.mocked(apiClient.delete).mockResolvedValueOnce(mockResponse)

        await documentService.deleteDocument('1')
        
        expect(apiClient.delete).toHaveBeenCalledWith('/documents/1')
      })
    })

    describe('searchDocuments', () => {
      it('searches documents with query', async () => {
        const mockResponse = {
          items: [
            { id: 1, name: 'Test Document', type: 'pdf' },
            { id: 2, name: 'Another Test', type: 'docx' }
          ],
          total: 2
        }
        
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse)

        const result = await documentService.searchDocuments({ query: 'test', page: 1, pageSize: 20 })
        
        expect(apiClient.get).toHaveBeenCalled()
        expect(result).toEqual(mockResponse)
      })
    })

    describe('getDocumentStats', () => {
      it('fetches document statistics', async () => {
        const mockStats = {
          total: 100,
          byType: { pdf: 50, docx: 30, xlsx: 20 },
          byStatus: { active: 80, archived: 20 },
          byTag: { important: 25, work: 40 },
          recentUploads: 10
        }
        
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockStats)

        const result = await documentService.getDocumentStats()
        
        expect(apiClient.get).toHaveBeenCalledWith('/documents/stats')
        expect(result).toEqual(mockStats)
      })
    })

    describe('previewDocument', () => {
      it('previews document content', async () => {
        const mockContent = '<html>Document content</html>'
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockContent)

        const result = await documentService.previewDocument('1', 1)
        
        expect(apiClient.get).toHaveBeenCalledWith('/documents/1/preview?page=1')
        expect(result).toEqual(mockContent)
      })

      it('previews document without page parameter', async () => {
        const mockContent = '<html>Document content</html>'
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockContent)

        const result = await documentService.previewDocument('1')
        
        expect(apiClient.get).toHaveBeenCalledWith('/documents/1/preview')
        expect(result).toEqual(mockContent)
      })
    })

    describe('getRelatedDocuments', () => {
      it('fetches related documents', async () => {
        const mockDocuments = [
          { id: 2, name: 'Related Document 1', type: 'pdf' },
          { id: 3, name: 'Related Document 2', type: 'docx' }
        ]
        
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockDocuments)

        const result = await documentService.getRelatedDocuments('1', 5)
        
        expect(apiClient.get).toHaveBeenCalledWith('/documents/1/related?limit=5')
        expect(result).toEqual(mockDocuments)
      })
    })

    describe('batch operations', () => {
      it('updates documents status in batch', async () => {
        vi.mocked(apiClient.put).mockResolvedValueOnce(undefined)

        await documentService.updateDocumentsStatus(['1', '2', '3'], 'archived')
        
        expect(apiClient.put).toHaveBeenCalledWith('/documents/batch/status', {
          documentIds: ['1', '2', '3'],
          status: 'archived'
        })
      })

      it('updates documents tags in batch', async () => {
        vi.mocked(apiClient.put).mockResolvedValueOnce(undefined)

        await documentService.batchUpdateTags(
          ['1', '2'], 
          ['important', 'reviewed'], 
          'add'
        )
        
        expect(apiClient.put).toHaveBeenCalledWith('/documents/batch/tags', {
          documentIds: ['1', '2'],
          tags: ['important', 'reviewed'],
          operation: 'add'
        })
      })
    })
  })
})