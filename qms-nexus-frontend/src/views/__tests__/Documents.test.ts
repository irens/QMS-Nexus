/**
 * Documents组件单元测试
 * 测试文档列表、搜索、筛选、分页等功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import Documents from '../Documents.vue'
import { useDocumentStore } from '@/stores/document'
import { documentService } from '@/services/document'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve())
  }
}))

// Mock documentService
vi.mock('@/services/document', () => ({
  documentService: {
    getDocuments: vi.fn(),
    getDocument: vi.fn(),
    deleteDocument: vi.fn(),
    updateDocumentTags: vi.fn(),
    downloadDocument: vi.fn()
  }
}))

// Mock router
const mockRouter = {
  push: vi.fn()
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter
}))

describe('Documents.vue', () => {
  let wrapper: VueWrapper<any>
  let documentStore: ReturnType<typeof useDocumentStore>

  // 模拟文档数据
  const mockDocuments = [
    {
      id: '1',
      filename: 'ISO13485.pdf',
      fileType: 'pdf',
      fileSize: 5242880,
      uploadTime: '2024-01-15T10:00:00Z',
      status: 'Completed',
      tags: ['quality', 'standard'],
      metadata: { pages: 45 }
    },
    {
      id: '2',
      filename: '质量手册.docx',
      fileType: 'docx',
      fileSize: 2097152,
      uploadTime: '2024-01-14T09:30:00Z',
      status: 'Processing',
      tags: ['quality', 'medical'],
      metadata: { pages: 32 }
    },
    {
      id: '3',
      filename: '检验标准.xlsx',
      fileType: 'xlsx',
      fileSize: 1048576,
      uploadTime: '2024-01-13T14:20:00Z',
      status: 'Completed',
      tags: ['standard', 'training'],
      metadata: { pages: 15 }
    }
  ]

  beforeEach(() => {
    // 创建新的 Pinia 实例
    setActivePinia(createPinia())
    documentStore = useDocumentStore()
    
    // 清理所有 mocks
    vi.clearAllMocks()
    
    // 模拟 API 响应
    vi.mocked(documentService.getDocuments).mockResolvedValue({
      items: mockDocuments,
      total: mockDocuments.length,
      page: 1,
      pageSize: 20
    })
    
    // 挂载组件
    wrapper = mount(Documents, {
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-input': true,
          'el-select': true,
          'el-option': true,
          'el-date-picker': true,
          'el-table': true,
          'el-table-column': true,
          'el-tag': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-pagination': true,
          'el-row': true,
          'el-col': true,
          'el-space': true,
          'el-dialog': true,
          'el-result': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper.unmount()
  })

  // ========================================
  // 1. 组件渲染测试
  // ========================================
  
  describe('组件渲染', () => {
    it('应该正确渲染页面标题', () => {
      expect(wrapper.text()).toContain('文档列表')
      expect(wrapper.text()).toContain('管理和查看已上传的文档')
    })

    it('应该显示搜索和筛选区域', () => {
      // 使用更具体的选择器来查找组件
      const searchInput = wrapper.findComponent({ name: 'ElInput' })
      const typeSelect = wrapper.findAllComponents({ name: 'ElSelect' })[0]
      const tagSelect = wrapper.findAllComponents({ name: 'ElSelect' })[1]
      const datePicker = wrapper.findComponent({ name: 'ElDatePicker' })
      
      expect(searchInput.exists()).toBe(true)
      expect(typeSelect.exists()).toBe(true)
      expect(tagSelect.exists()).toBe(true)
      expect(datePicker.exists()).toBe(true)
    })

    it('应该显示搜索和重置按钮', () => {
      const buttons = wrapper.findAllComponents({ name: 'ElButton' })
      const searchButton = buttons.find(btn => btn.props('type') === 'primary')
      const resetButton = buttons.find(btn => btn.text().includes('重置'))
      
      expect(searchButton?.exists()).toBe(true)
      expect(searchButton?.text()).toContain('搜索')
      expect(resetButton?.exists()).toBe(true)
    })
  })

  // ========================================
  // 2. 文档列表测试
  // ========================================
  
  describe('文档列表', () => {
    it('应该正确显示文档列表', async () => {
      await wrapper.vm.fetchDocuments()
      await wrapper.vm.$nextTick()
      
      expect(documentStore.documents).toHaveLength(3)
      expect(wrapper.vm.documents).toHaveLength(3)
    })

    it('应该显示加载状态', async () => {
      // 模拟加载状态
      documentStore.loading = true
      await wrapper.vm.$nextTick()
      
      expect(wrapper.find('.el-loading-mask').exists()).toBe(true)
    })

    it('应该显示空列表提示', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        pageSize: 20
      })
      
      await wrapper.vm.fetchDocuments()
      await wrapper.vm.$nextTick()
      
      expect(documentStore.documents).toHaveLength(0)
      expect(wrapper.vm.documents).toHaveLength(0)
    })

    it('应该显示文档信息', async () => {
      await wrapper.vm.fetchDocuments()
      await wrapper.vm.$nextTick()
      
      const firstDoc = wrapper.vm.documents[0]
      expect(firstDoc.filename).toBe('ISO13485.pdf')
      expect(firstDoc.fileType).toBe('pdf')
      expect(firstDoc.fileSize).toBe(5242880)
    })
  })

  // ========================================
  // 3. 搜索和筛选测试
  // ========================================
  
  describe('搜索和筛选功能', () => {
    it('应该根据关键词搜索文档', async () => {
      wrapper.vm.searchQuery = 'ISO13485'
      await wrapper.vm.handleSearch()
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'ISO13485'
        })
      )
    })

    it('应该按文件类型筛选', async () => {
      wrapper.vm.selectedType = 'pdf'
      await wrapper.vm.handleSearch()
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          fileType: ['pdf']
        })
      )
    })

    it('应该按标签筛选', async () => {
      wrapper.vm.selectedTag = 'quality'
      await wrapper.vm.handleSearch()
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          tags: ['quality']
        })
      )
    })

    it('应该按日期范围筛选', async () => {
      wrapper.vm.dateRange = ['2024-01-01', '2024-01-31']
      await wrapper.vm.handleSearch()
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          dateRange: ['2024-01-01', '2024-01-31']
        })
      )
    })

    it('应该重置所有筛选条件', async () => {
      wrapper.vm.searchQuery = 'test'
      wrapper.vm.selectedType = 'pdf'
      wrapper.vm.selectedTag = 'quality'
      wrapper.vm.dateRange = ['2024-01-01', '2024-01-31']
      
      await wrapper.vm.resetFilters()
      
      expect(wrapper.vm.searchQuery).toBe('')
      expect(wrapper.vm.selectedType).toBe('')
      expect(wrapper.vm.selectedTag).toBe('')
      expect(wrapper.vm.dateRange).toBeNull()
    })
  })

  // ========================================
  // 4. 分页功能测试
  // ========================================
  
  describe('分页功能', () => {
    it('应该正确计算总页数', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: 100,
        page: 1,
        pageSize: 20
      })
      
      await wrapper.vm.fetchDocuments()
      await wrapper.vm.$nextTick()
      
      expect(documentStore.totalPages).toBe(5) // 100 / 20 = 5
    })

    it('应该切换到指定页码', async () => {
      await wrapper.vm.handleCurrentChange(2)
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2
        })
      )
    })

    it('应该改变每页显示数量', async () => {
      await wrapper.vm.handleSizeChange(50)
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          pageSize: 50,
          page: 1 // 应该重置到第一页
        })
      )
    })

    it('应该显示分页控件', () => {
      const pagination = wrapper.find('el-pagination')
      expect(pagination.exists()).toBe(true)
    })
  })

  // ========================================
  // 5. 文档选择测试
  // ========================================
  
  describe('文档选择', () => {
    it('应该正确选择文档', async () => {
      await wrapper.vm.fetchDocuments()
      
      const docId = wrapper.vm.documents[0].id
      wrapper.vm.selectedIds = [docId]
      
      await wrapper.vm.$nextTick()
      
      expect(wrapper.vm.selectedDocuments).toHaveLength(1)
      expect(wrapper.vm.selectedDocuments[0].id).toBe(docId)
    })

    it('应该显示批量操作按钮', async () => {
      await wrapper.vm.fetchDocuments()
      
      wrapper.vm.selectedIds = ['1', '2']
      await wrapper.vm.$nextTick()
      
      expect(wrapper.find('.batch-operations').exists()).toBe(true)
    })

    it('应该显示选中数量', async () => {
      await wrapper.vm.fetchDocuments()
      
      wrapper.vm.selectedIds = ['1', '2', '3']
      await wrapper.vm.$nextTick()
      
      expect(wrapper.text()).toContain('已选择 3 个')
    })
  })

  // ========================================
  // 6. 文档操作测试
  // ========================================
  
  describe('文档操作', () => {
    beforeEach(async () => {
      await wrapper.vm.fetchDocuments()
    })

    it('应该查看文档详情', () => {
      const doc = wrapper.vm.documents[0]
      wrapper.vm.viewDocument(doc)
      
      expect(mockRouter.push).toHaveBeenCalledWith(`/system/documents/${doc.id}`)
    })

    it('应该下载文档', async () => {
      vi.mocked(documentService.downloadDocument).mockResolvedValue(true)
      
      const doc = wrapper.vm.documents[0]
      await wrapper.vm.downloadDocument(doc)
      
      expect(documentService.downloadDocument).toHaveBeenCalledWith(doc.id, doc.filename)
      expect(ElMessage.success).toHaveBeenCalledWith(`开始下载: ${doc.filename}`)
    })

    it('应该处理下载失败', async () => {
      vi.mocked(documentService.downloadDocument).mockResolvedValue(false)
      
      const doc = wrapper.vm.documents[0]
      await wrapper.vm.downloadDocument(doc)
      
      expect(ElMessage.error).toHaveBeenCalledWith('下载失败')
    })

    it('应该删除文档', async () => {
      vi.mocked(documentService.deleteDocument).mockResolvedValue({ success: true })
      vi.mocked(ElMessageBox.confirm).mockResolvedValue(undefined)
      
      const doc = wrapper.vm.documents[0]
      await wrapper.vm.deleteDocument(doc)
      
      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(documentService.deleteDocument).toHaveBeenCalledWith(doc.id)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('应该取消删除操作', async () => {
      vi.mocked(ElMessageBox.confirm).mockRejectedValue(new Error('cancel'))
      
      const doc = wrapper.vm.documents[0]
      await wrapper.vm.deleteDocument(doc).catch(() => {})
      
      expect(documentService.deleteDocument).not.toHaveBeenCalled()
    })
  })

  // ========================================
  // 7. 批量操作测试
  // ========================================
  
  describe('批量操作', () => {
    beforeEach(async () => {
      await wrapper.vm.fetchDocuments()
      wrapper.vm.selectedIds = ['1', '2']
    })

    it('应该批量删除文档', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue(undefined)
      vi.mocked(documentService.deleteDocument).mockResolvedValue({ success: true })
      
      await wrapper.vm.batchDelete()
      
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除选中的 2 个文档吗？',
        '确认批量删除',
        expect.any(Object)
      )
      expect(documentService.deleteDocument).toHaveBeenCalledTimes(2)
      expect(ElMessage.success).toHaveBeenCalledWith('批量删除成功')
    })

    it('应该批量下载文档', async () => {
      vi.mocked(documentService.downloadDocument).mockResolvedValue(true)
      
      await wrapper.vm.batchDownload()
      
      expect(documentService.downloadDocument).toHaveBeenCalledTimes(2)
      expect(ElMessage.success).toHaveBeenCalledWith('批量下载完成')
    })

    it('应该处理批量下载中的失败', async () => {
      vi.mocked(documentService.downloadDocument)
        .mockResolvedValueOnce(true)
        .mockRejectedValueOnce(new Error('Download failed'))
      
      await wrapper.vm.batchDownload()
      
      expect(ElMessage.error).toHaveBeenCalledWith('下载失败: 质量手册.docx')
    })
  })

  // ========================================
  // 8. 标签管理测试
  // ========================================
  
  describe('标签管理', () => {
    beforeEach(async () => {
      await wrapper.vm.fetchDocuments()
    })

    it('应该正确显示标签', () => {
      const doc = wrapper.vm.documents[0]
      expect(doc.tags).toContain('quality')
      expect(doc.tags).toContain('standard')
    })

    it('应该根据标签筛选', async () => {
      wrapper.vm.filterByTag('quality')
      
      expect(wrapper.vm.selectedTag).toBe('quality')
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          tags: ['quality']
        })
      )
    })

    it('应该获取标签类型', () => {
      expect(wrapper.vm.getTagType('quality')).toBe('primary')
      expect(wrapper.vm.getTagType('medical')).toBe('success')
      expect(wrapper.vm.getTagType('training')).toBe('warning')
    })

    it('应该获取标签文本', () => {
      expect(wrapper.vm.getTagText('quality')).toBe('质量管理')
      expect(wrapper.vm.getTagText('medical')).toBe('医疗规范')
      expect(wrapper.vm.getTagText('standard')).toBe('标准规范')
    })
  })

  // ========================================
  // 9. 错误处理测试
  // ========================================
  
  describe('错误处理', () => {
    it('应该处理API调用失败', async () => {
      vi.mocked(documentService.getDocuments).mockRejectedValue(
        new Error('Network error')
      )
      
      await wrapper.vm.fetchDocuments()
      
      expect(documentStore.error).toBe('Network error')
      expect(ElMessage.error).toHaveBeenCalledWith('获取文档列表失败')
    })

    it('应该显示加载错误状态', async () => {
      vi.mocked(documentService.getDocuments).mockRejectedValue(
        new Error('API Error')
      )
      
      await wrapper.vm.fetchDocuments()
      await wrapper.vm.$nextTick()
      
      expect(wrapper.text()).toContain('获取文档列表失败')
    })
  })

  // ========================================
  // 10. 辅助函数测试
  // ========================================
  
  describe('辅助函数', () => {
    it('应该正确格式化文件大小', () => {
      expect(wrapper.vm.formatFileSize(0)).toBe('0 B')
      expect(wrapper.vm.formatFileSize(1024)).toBe('1 KB')
      expect(wrapper.vm.formatFileSize(1024 * 1024)).toBe('1 MB')
      expect(wrapper.vm.formatFileSize(1024 * 1024 * 1024)).toBe('1 GB')
      expect(wrapper.vm.formatFileSize(1024 * 1024 * 1024 * 1.5)).toBe('1.5 GB')
    })

    it('应该正确获取文件图标', () => {
      expect(wrapper.vm.getFileIcon('pdf')).toBeDefined()
      expect(wrapper.vm.getFileIcon('docx')).toBeDefined()
      expect(wrapper.vm.getFileIcon('xlsx')).toBeDefined()
      expect(wrapper.vm.getFileIcon('pptx')).toBeDefined()
    })

    it('应该正确获取文件图标颜色', () => {
      expect(wrapper.vm.getFileIconColor('pdf')).toBe('text-red-600')
      expect(wrapper.vm.getFileIconColor('docx')).toBe('text-blue-600')
      expect(wrapper.vm.getFileIconColor('xlsx')).toBe('text-green-600')
      expect(wrapper.vm.getFileIconColor('pptx')).toBe('text-orange-600')
    })

    it('应该正确获取状态类型', () => {
      expect(wrapper.vm.getStatusType('Processing')).toBe('warning')
      expect(wrapper.vm.getStatusType('Completed')).toBe('success')
      expect(wrapper.vm.getStatusType('Failed')).toBe('danger')
    })

    it('应该正确获取状态文本', () => {
      expect(wrapper.vm.getStatusText('Processing')).toBe('解析中')
      expect(wrapper.vm.getStatusText('Completed')).toBe('已完成')
      expect(wrapper.vm.getStatusText('Failed')).toBe('失败')
    })
  })
})
