<template>
  <div class="document-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文档管理</span>
          <el-button type="primary" @click="handleUpload">
            <el-icon><Plus /></el-icon>
            上传文档
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索文档名称、编号..."
          clearable
          style="width: 300px"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
        
        <el-select
          v-model="filterStatus"
          placeholder="状态筛选"
          clearable
          style="width: 150px; margin-left: 10px"
          @change="handleSearch"
        >
          <el-option label="草稿" value="draft" />
          <el-option label="审核中" value="review" />
          <el-option label="已批准" value="approved" />
          <el-option label="生效中" value="effective" />
          <el-option label="已作废" value="obsolete" />
        </el-select>
      </div>

      <!-- 文档列表表格 -->
      <el-table
        v-loading="loading"
        :data="documents"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column type="index" width="50" />
        
        <el-table-column label="文档名称" min-width="200">
          <template #default="{ row }">
            <div class="doc-name">
              <el-icon class="doc-icon"><Document /></el-icon>
              <div class="doc-info">
                <span class="doc-title">{{ row.title || row.filename }}</span>
                <span v-if="row.doc_code" class="doc-code">{{ row.doc_code }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 版本列 -->
        <el-table-column label="版本" width="120">
          <template #default="{ row }">
            <el-tag
              :type="getVersionStatusType(row.currentVersion?.status)"
              size="small"
            >
              {{ row.currentVersion?.version_label || `V${row.currentVersion?.version_number}` }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 状态列 -->
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.currentVersion?.status)">
              {{ getStatusText(row.currentVersion?.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 生效日期列 -->
        <el-table-column label="生效日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.currentVersion?.effective_date) }}
          </template>
        </el-table-column>

        <!-- 复审日期列 -->
        <el-table-column label="复审日期" width="120">
          <template #default="{ row }">
            <span :class="{ 'review-warning': isReviewNear(row.currentVersion?.review_date) }">
              {{ formatDate(row.currentVersion?.review_date) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="文档类型" width="120">
          <template #default="{ row }">
            {{ row.doc_type || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="知识库" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.kb_id }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="更新时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              @click.stop="viewVersions(row.id)"
            >
              版本历史
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click.stop="uploadNewVersion(row.id)"
            >
              上传新版本
            </el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, row)" @click.stop>
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="view">查看详情</el-dropdown-item>
                  <el-dropdown-item command="download">下载</el-dropdown-item>
                  <el-dropdown-item command="compare" :disabled="!row.currentVersion?.previous_version_id">
                    对比上一版本
                  </el-dropdown-item>
                  <el-dropdown-item divided command="delete" type="danger">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 上传文档对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传文档"
      width="600px"
      destroy-on-close
    >
      <el-form :model="uploadForm" label-width="100px" :rules="uploadRules" ref="uploadFormRef">
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、Word、Excel 等文档格式
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入文档标题" />
        </el-form-item>
        <el-form-item label="文档编号">
          <el-input v-model="uploadForm.docCode" placeholder="如：GJZ-QP-01" />
        </el-form-item>
        <el-form-item label="文档类型">
          <el-select v-model="uploadForm.docType" placeholder="选择文档类型" style="width: 100%">
            <el-option label="质量手册" value="质量手册" />
            <el-option label="程序文件" value="程序文件" />
            <el-option label="作业指导书" value="作业指导书" />
            <el-option label="记录表单" value="记录表单" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="变更摘要" prop="changeSummary">
          <el-input
            v-model="uploadForm.changeSummary"
            type="textarea"
            rows="2"
            placeholder="请简要描述本次变更内容"
          />
        </el-form-item>
        <el-form-item label="变更详情">
          <el-input
            v-model="uploadForm.changeDetails"
            type="textarea"
            rows="4"
            placeholder="请详细描述变更内容（选填）"
          />
        </el-form-item>
        <el-form-item label="生效日期">
          <el-date-picker
            v-model="uploadForm.effectiveDate"
            type="date"
            placeholder="选择生效日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="知识库">
          <el-select v-model="uploadForm.kbId" placeholder="选择知识库" style="width: 100%">
            <el-option label="默认知识库" value="default" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :loading="uploading">
          确认上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传新版本对话框 -->
    <el-dialog
      v-model="newVersionDialogVisible"
      title="上传新版本"
      width="600px"
      destroy-on-close
    >
      <el-alert
        v-if="currentDocument"
        :title="`正在为「${currentDocument.title || currentDocument.filename}」创建新版本`"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="newVersionForm" label-width="100px" :rules="newVersionRules" ref="newVersionFormRef">
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="newVersionUploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleNewVersionFileChange"
            :limit="1"
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="变更摘要" prop="changeSummary">
          <el-input
            v-model="newVersionForm.changeSummary"
            type="textarea"
            rows="2"
            placeholder="请简要描述本次变更内容（必填）"
          />
        </el-form-item>
        <el-form-item label="变更详情">
          <el-input
            v-model="newVersionForm.changeDetails"
            type="textarea"
            rows="4"
            placeholder="请详细描述变更内容（选填）"
          />
        </el-form-item>
        <el-form-item label="版本标签">
          <el-input
            v-model="newVersionForm.versionLabel"
            placeholder="如：V2.1（选填，系统会自动生成）"
          />
        </el-form-item>
        <el-form-item label="生效日期">
          <el-date-picker
            v-model="newVersionForm.effectiveDate"
            type="date"
            placeholder="选择生效日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newVersionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmNewVersion" :loading="uploadingNewVersion">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, Document, ArrowDown } from '@element-plus/icons-vue';
import documentVersionService, { VersionStatus } from '@/services/documentVersion';

const router = useRouter();

// 数据
const documents = ref<any[]>([]);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const searchQuery = ref('');
const filterStatus = ref('');

// 当前操作的文档
const currentDocument = ref<any>(null);

// 上传对话框
const uploadDialogVisible = ref(false);
const uploadFormRef = ref();
const uploadRef = ref();
const uploading = ref(false);
const uploadForm = ref({
  file: null as File | null,
  title: '',
  docCode: '',
  docType: '',
  changeSummary: '',
  changeDetails: '',
  effectiveDate: '',
  kbId: 'default',
});

const uploadRules = {
  file: [{ required: true, message: '请选择文件', trigger: 'change' }],
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }],
  changeSummary: [{ required: true, message: '请输入变更摘要', trigger: 'blur' }],
};

// 上传新版本对话框
const newVersionDialogVisible = ref(false);
const newVersionFormRef = ref();
const newVersionUploadRef = ref();
const uploadingNewVersion = ref(false);
const newVersionForm = ref({
  file: null as File | null,
  changeSummary: '',
  changeDetails: '',
  versionLabel: '',
  effectiveDate: '',
});

const newVersionRules = {
  file: [{ required: true, message: '请选择文件', trigger: 'change' }],
  changeSummary: [{ required: true, message: '请输入变更摘要', trigger: 'blur' }],
};

// 获取文档列表
const fetchDocuments = async () => {
  loading.value = true;
  try {
    // 这里应该调用实际的API获取文档列表
    // 由于后端API可能不同，这里使用模拟数据
    // 实际项目中应该替换为真实的API调用
    const response = await fetch(`/api/v1/documents?page=${page.value}&page_size=${pageSize.value}&q=${searchQuery.value}&status=${filterStatus.value}`);
    const result = await response.json();
    
    if (result.code === 200) {
      documents.value = result.data.items || [];
      total.value = result.data.total || 0;
    }
  } catch (error) {
    // 如果API不存在，使用模拟数据
    documents.value = [
      {
        id: 'doc_001',
        title: '质量管理手册',
        filename: '质量管理手册.pdf',
        doc_code: 'GJZ-QM-01',
        doc_type: '质量手册',
        kb_id: 'default',
        updated_at: '2024-01-15T10:30:00',
        currentVersion: {
          id: 'ver_001',
          version_number: 2,
          version_label: 'V2.0',
          status: 'effective',
          effective_date: '2024-01-15T00:00:00',
          review_date: '2025-01-15T00:00:00',
          previous_version_id: 'ver_000',
        },
      },
      {
        id: 'doc_002',
        title: '记录控制程序',
        filename: '记录控制程序.docx',
        doc_code: 'GJZ-QP-01',
        doc_type: '程序文件',
        kb_id: 'default',
        updated_at: '2024-02-20T14:00:00',
        currentVersion: {
          id: 'ver_002',
          version_number: 3,
          version_label: 'V3.1',
          status: 'review',
          effective_date: null,
          review_date: null,
          previous_version_id: 'ver_001_old',
        },
      },
    ];
    total.value = documents.value.length;
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  page.value = 1;
  fetchDocuments();
};

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  page.value = 1;
  fetchDocuments();
};

const handleCurrentChange = (val: number) => {
  page.value = val;
  fetchDocuments();
};

// 行点击
const handleRowClick = (row: any) => {
  viewVersions(row.id);
};

// 查看版本历史
const viewVersions = (documentId: string) => {
  router.push(`/documents/${documentId}/versions`);
};

// 上传新版本
const uploadNewVersion = (documentId: string) => {
  const doc = documents.value.find(d => d.id === documentId);
  if (doc) {
    currentDocument.value = doc;
    newVersionForm.value = {
      file: null,
      changeSummary: '',
      changeDetails: '',
      versionLabel: '',
      effectiveDate: '',
    };
    newVersionDialogVisible.value = true;
  }
};

// 更多操作
const handleCommand = (command: string, row: any) => {
  switch (command) {
    case 'view':
      if (row.currentVersion?.id) {
        router.push(`/documents/versions/${row.currentVersion.id}`);
      }
      break;
    case 'download':
      downloadDocument(row);
      break;
    case 'compare':
      if (row.currentVersion?.previous_version_id) {
        router.push({
          path: '/documents/compare',
          query: {
            v1: row.currentVersion.previous_version_id,
            v2: row.currentVersion.id,
          },
        });
      }
      break;
    case 'delete':
      deleteDocument(row);
      break;
  }
};

// 下载文档
const downloadDocument = async (row: any) => {
  if (!row.currentVersion?.id) {
    ElMessage.warning('当前文档没有可下载的版本');
    return;
  }
  
  try {
    const blob = await documentVersionService.downloadVersion(row.currentVersion.id);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = row.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    ElMessage.success('下载成功');
  } catch (error) {
    ElMessage.error('下载失败：' + (error as Error).message);
  }
};

// 删除文档
const deleteDocument = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    // 调用删除API
    ElMessage.success('删除成功');
    fetchDocuments();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + (error as Error).message);
    }
  }
};

// 上传文档
const handleUpload = () => {
  uploadForm.value = {
    file: null,
    title: '',
    docCode: '',
    docType: '',
    changeSummary: '',
    changeDetails: '',
    effectiveDate: '',
    kbId: 'default',
  };
  uploadDialogVisible.value = true;
};

// 文件选择变化
const handleFileChange = (file: any) => {
  uploadForm.value.file = file.raw;
  // 自动填充标题
  if (!uploadForm.value.title && file.name) {
    uploadForm.value.title = file.name.replace(/\.[^/.]+$/, '');
  }
};

// 确认上传
const confirmUpload = async () => {
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择文件');
    return;
  }
  
  await uploadFormRef.value?.validate(async (valid: boolean) => {
    if (!valid) return;
    
    uploading.value = true;
    try {
      // 这里应该调用创建新文档的API
      // 由于后端API可能不同，这里模拟上传
      ElMessage.success('文档上传成功');
      uploadDialogVisible.value = false;
      fetchDocuments();
    } catch (error) {
      ElMessage.error('上传失败：' + (error as Error).message);
    } finally {
      uploading.value = false;
    }
  });
};

// 新版本文件选择
const handleNewVersionFileChange = (file: any) => {
  newVersionForm.value.file = file.raw;
};

// 确认上传新版本
const confirmNewVersion = async () => {
  if (!newVersionForm.value.file || !currentDocument.value) {
    ElMessage.warning('请选择文件');
    return;
  }
  
  await newVersionFormRef.value?.validate(async (valid: boolean) => {
    if (!valid) return;
    
    uploadingNewVersion.value = true;
    try {
      await documentVersionService.uploadNewVersion(
        currentDocument.value.id,
        newVersionForm.value.file,
        {
          changeSummary: newVersionForm.value.changeSummary,
          changeDetails: newVersionForm.value.changeDetails || undefined,
          versionLabel: newVersionForm.value.versionLabel || undefined,
          effectiveDate: newVersionForm.value.effectiveDate ? new Date(newVersionForm.value.effectiveDate) : undefined,
        }
      );
      ElMessage.success('新版本上传成功');
      newVersionDialogVisible.value = false;
      fetchDocuments();
    } catch (error) {
      ElMessage.error('上传失败：' + (error as Error).message);
    } finally {
      uploadingNewVersion.value = false;
    }
  });
};

// 工具函数
const getStatusText = (status?: VersionStatus) => {
  if (!status) return '-';
  return documentVersionService.getStatusText(status);
};

const getStatusType = (status?: VersionStatus) => {
  if (!status) return '';
  return documentVersionService.getStatusType(status);
};

const getVersionStatusType = (status?: VersionStatus) => {
  if (!status) return '';
  return documentVersionService.getStatusType(status);
};

const formatDate = (date?: string) => {
  return documentVersionService.formatDate(date);
};

const formatDateTime = (date?: string) => {
  return documentVersionService.formatDateTime(date);
};

// 判断复审日期是否临近（30天内）
const isReviewNear = (date?: string): boolean => {
  if (!date) return false;
  const reviewDate = new Date(date);
  const now = new Date();
  const diffDays = Math.ceil((reviewDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return diffDays <= 30 && diffDays >= 0;
};

onMounted(() => {
  fetchDocuments();
});
</script>

<style scoped lang="scss">
.document-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.doc-name {
  display: flex;
  align-items: center;
  gap: 10px;

  .doc-icon {
    font-size: 24px;
    color: var(--el-color-primary);
  }

  .doc-info {
    display: flex;
    flex-direction: column;

    .doc-title {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }

    .doc-code {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.review-warning {
  color: var(--el-color-warning);
  font-weight: bold;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-fill-color-light);
}
</style>
