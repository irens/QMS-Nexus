<template>
  <div class="version-history">
    <el-page-header @back="goBack" :content="pageTitle" />
    
    <el-card class="version-list-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>版本历史</span>
          <el-button type="primary" @click="handleUploadNewVersion">
            <el-icon><Plus /></el-icon>
            上传新版本
          </el-button>
        </div>
      </template>

      <!-- 版本时间轴 -->
      <el-timeline v-if="versions.length > 0">
        <el-timeline-item
          v-for="version in versions"
          :key="version.id"
          :type="getTimelineItemType(version.status)"
          :timestamp="formatDateTime(version.created_at)"
          placement="top"
        >
          <el-card class="version-card" :class="{ 'latest-version': version.is_latest }">
            <div class="version-header">
              <div class="version-info-left">
                <span class="version-label">{{ version.version_label || `V${version.version_number}` }}</span>
                <el-tag :type="getStatusType(version.status)" size="small">
                  {{ getStatusText(version.status) }}
                </el-tag>
                <el-tag v-if="version.is_latest" type="success" size="small" effect="dark">
                  最新
                </el-tag>
              </div>
              <div class="version-actions">
                <el-button 
                  size="small" 
                  @click="viewDetail(version.id)"
                  :icon="View"
                >
                  查看详情
                </el-button>
                <el-button 
                  size="small" 
                  @click="downloadVersion(version.id, version.filename)"
                  :icon="Download"
                >
                  下载
                </el-button>
                <el-button
                  v-if="canCompare(version)"
                  size="small"
                  type="info"
                  @click="compareWithPrevious(version)"
                  :icon="Switch"
                >
                  对比上一版本
                </el-button>
                <el-button
                  v-if="canSubmitForReview(version)"
                  size="small"
                  type="warning"
                  @click="submitForReview(version)"
                >
                  提交审核
                </el-button>
                <el-button
                  v-if="canApprove(version)"
                  size="small"
                  type="success"
                  @click="approveVersion(version)"
                >
                  审批通过
                </el-button>
                <el-button
                  v-if="canReject(version)"
                  size="small"
                  type="danger"
                  @click="rejectVersion(version)"
                >
                  拒绝
                </el-button>
                <el-button
                  v-if="canObsolete(version)"
                  size="small"
                  type="danger"
                  plain
                  @click="obsoleteVersion(version)"
                >
                  作废
                </el-button>
              </div>
            </div>
            
            <div class="version-info">
              <p><strong>文件名：</strong>{{ version.filename }}</p>
              <p v-if="version.change_summary">
                <strong>变更摘要：</strong>{{ version.change_summary }}
              </p>
              <p v-if="version.change_details">
                <strong>变更详情：</strong>{{ version.change_details }}
              </p>
              <p><strong>生效日期：</strong>{{ formatDate(version.effective_date) || '未设置' }}</p>
              <p><strong>编制人：</strong>{{ version.prepared_by || '-' }}</p>
              <p v-if="version.approved_by">
                <strong>批准人：</strong>{{ version.approved_by }}
                <span v-if="version.approved_date">（{{ formatDateTime(version.approved_date) }}）</span>
              </p>
              <p><strong>文件大小：</strong>{{ formatFileSize(version.file_size) }}</p>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <!-- 空状态 -->
      <el-empty v-else description="暂无版本历史" />

      <!-- 分页 -->
      <div class="pagination-container" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 上传新版本对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传新版本"
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
        <el-form-item label="版本标签">
          <el-input
            v-model="uploadForm.versionLabel"
            placeholder="如：V2.1（选填，系统会自动生成）"
          />
        </el-form-item>
        <el-form-item label="生效日期">
          <el-date-picker
            v-model="uploadForm.effectiveDate"
            type="date"
            placeholder="选择生效日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :loading="uploading">
          确认上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 审批对话框 -->
    <el-dialog
      v-model="approveDialogVisible"
      title="审批意见"
      width="500px"
    >
      <el-input
        v-model="approvalComment"
        type="textarea"
        rows="4"
        :placeholder="approvalAction === 'reject' ? '请输入拒绝原因（必填）' : '请输入审批意见（选填）'"
      />
      <template #footer>
        <el-button @click="approveDialogVisible = false">取消</el-button>
        <el-button 
          :type="approvalAction === 'approve' ? 'success' : 'danger'" 
          @click="confirmApproval"
          :loading="approvalLoading"
        >
          {{ approvalAction === 'approve' ? '确认通过' : '确认拒绝' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 作废对话框 -->
    <el-dialog
      v-model="obsoleteDialogVisible"
      title="作废版本"
      width="500px"
    >
      <el-input
        v-model="obsoleteReason"
        type="textarea"
        rows="4"
        placeholder="请输入作废原因（选填）"
      />
      <template #footer>
        <el-button @click="obsoleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmObsolete" :loading="obsoleteLoading">
          确认作废
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, View, Download, Switch } from '@element-plus/icons-vue';
import documentVersionService, { Version, VersionStatus } from '@/services/documentVersion';

const route = useRoute();
const router = useRouter();

// 文档信息
const documentId = computed(() => route.params.id as string);
const documentTitle = ref('');
const pageTitle = computed(() => `${documentTitle.value} - 版本历史`);

// 版本列表数据
const versions = ref<Version[]>([]);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 上传对话框
const uploadDialogVisible = ref(false);
const uploadFormRef = ref();
const uploadRef = ref();
const uploading = ref(false);
const uploadForm = ref({
  file: null as File | null,
  changeSummary: '',
  changeDetails: '',
  versionLabel: '',
  effectiveDate: '',
});

const uploadRules = {
  changeSummary: [{ required: true, message: '请输入变更摘要', trigger: 'blur' }],
};

// 审批对话框
const approveDialogVisible = ref(false);
const approvalLoading = ref(false);
const approvalComment = ref('');
const approvalAction = ref<'approve' | 'reject'>('approve');
const currentVersion = ref<Version | null>(null);

// 作废对话框
const obsoleteDialogVisible = ref(false);
const obsoleteLoading = ref(false);
const obsoleteReason = ref('');

// 获取版本列表
const fetchVersions = async () => {
  if (!documentId.value) return;
  
  loading.value = true;
  try {
    const response = await documentVersionService.getDocumentVersions(documentId.value, {
      page: page.value,
      pageSize: pageSize.value,
      sortBy: 'version_number',
      sortOrder: 'desc',
    });
    versions.value = response.items;
    total.value = response.total;
    
    // 从第一个版本获取文档标题
    if (response.items.length > 0 && response.items[0].title) {
      documentTitle.value = response.items[0].title;
    }
  } catch (error) {
    ElMessage.error('获取版本列表失败：' + (error as Error).message);
  } finally {
    loading.value = false;
  }
};

// 返回上一页
const goBack = () => {
  router.back();
};

// 查看详情
const viewDetail = (versionId: string) => {
  router.push(`/documents/versions/${versionId}`);
};

// 下载版本
const downloadVersion = async (versionId: string, filename: string) => {
  try {
    const blob = await documentVersionService.downloadVersion(versionId);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    ElMessage.success('下载成功');
  } catch (error) {
    ElMessage.error('下载失败：' + (error as Error).message);
  }
};

// 对比上一版本
const compareWithPrevious = (version: Version) => {
  if (version.previous_version_id) {
    router.push({
      path: '/documents/compare',
      query: {
        v1: version.previous_version_id,
        v2: version.id,
      },
    });
  }
};

// 判断是否可以对比
const canCompare = (version: Version): boolean => {
  return !!version.previous_version_id;
};

// 判断是否可以提交审核
const canSubmitForReview = (version: Version): boolean => {
  return version.status === 'draft';
};

// 判断是否可以审批通过
const canApprove = (version: Version): boolean => {
  return version.status === 'review' || version.status === 'approved';
};

// 判断是否可以拒绝
const canReject = (version: Version): boolean => {
  return version.status === 'review';
};

// 判断是否可以作废
const canObsolete = (version: Version): boolean => {
  return version.status === 'effective' || version.status === 'approved';
};

// 提交审核
const submitForReview = async (version: Version) => {
  try {
    await ElMessageBox.confirm('确定要提交该版本进行审核吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    await documentVersionService.submitForReview(version.id);
    ElMessage.success('提交审核成功');
    fetchVersions();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交审核失败：' + (error as Error).message);
    }
  }
};

// 审批通过
const approveVersion = (version: Version) => {
  currentVersion.value = version;
  approvalAction.value = 'approve';
  approvalComment.value = '';
  approveDialogVisible.value = true;
};

// 拒绝版本
const rejectVersion = (version: Version) => {
  currentVersion.value = version;
  approvalAction.value = 'reject';
  approvalComment.value = '';
  approveDialogVisible.value = true;
};

// 确认审批
const confirmApproval = async () => {
  if (!currentVersion.value) return;
  
  if (approvalAction.value === 'reject' && !approvalComment.value.trim()) {
    ElMessage.warning('请输入拒绝原因');
    return;
  }
  
  approvalLoading.value = true;
  try {
    if (approvalAction.value === 'approve') {
      await documentVersionService.approveVersion(currentVersion.value.id, approvalComment.value);
      ElMessage.success('审批通过');
    } else {
      await documentVersionService.rejectVersion(currentVersion.value.id, approvalComment.value);
      ElMessage.success('已拒绝该版本');
    }
    approveDialogVisible.value = false;
    fetchVersions();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    approvalLoading.value = false;
  }
};

// 作废版本
const obsoleteVersion = (version: Version) => {
  currentVersion.value = version;
  obsoleteReason.value = '';
  obsoleteDialogVisible.value = true;
};

// 确认作废
const confirmObsolete = async () => {
  if (!currentVersion.value) return;
  
  obsoleteLoading.value = true;
  try {
    await documentVersionService.obsoleteVersion(currentVersion.value.id, obsoleteReason.value);
    ElMessage.success('版本已作废');
    obsoleteDialogVisible.value = false;
    fetchVersions();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    obsoleteLoading.value = false;
  }
};

// 上传新版本
const handleUploadNewVersion = () => {
  uploadForm.value = {
    file: null,
    changeSummary: '',
    changeDetails: '',
    versionLabel: '',
    effectiveDate: '',
  };
  uploadDialogVisible.value = true;
};

// 文件选择变化
const handleFileChange = (file: any) => {
  uploadForm.value.file = file.raw;
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
      await documentVersionService.uploadNewVersion(
        documentId.value,
        uploadForm.value.file,
        {
          changeSummary: uploadForm.value.changeSummary,
          changeDetails: uploadForm.value.changeDetails || undefined,
          versionLabel: uploadForm.value.versionLabel || undefined,
          effectiveDate: uploadForm.value.effectiveDate ? new Date(uploadForm.value.effectiveDate) : undefined,
        }
      );
      ElMessage.success('上传新版本成功');
      uploadDialogVisible.value = false;
      fetchVersions();
    } catch (error) {
      ElMessage.error('上传失败：' + (error as Error).message);
    } finally {
      uploading.value = false;
    }
  });
};

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val;
  page.value = 1;
  fetchVersions();
};

const handleCurrentChange = (val: number) => {
  page.value = val;
  fetchVersions();
};

// 工具函数
const getStatusText = (status: VersionStatus) => documentVersionService.getStatusText(status);
const getStatusType = (status: VersionStatus) => documentVersionService.getStatusType(status);
const getTimelineItemType = (status: VersionStatus) => documentVersionService.getTimelineItemType(status);
const formatDate = (date?: string) => documentVersionService.formatDate(date);
const formatDateTime = (date?: string) => documentVersionService.formatDateTime(date);
const formatFileSize = (bytes: number) => documentVersionService.formatFileSize(bytes);

onMounted(() => {
  fetchVersions();
});
</script>

<style scoped lang="scss">
.version-history {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.version-list-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.version-card {
  margin-bottom: 10px;
  
  &.latest-version {
    border: 1px solid var(--el-color-success);
  }
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.version-info-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.version-label {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.version-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.version-info {
  p {
    margin: 8px 0;
    color: var(--el-text-color-regular);
    
    strong {
      color: var(--el-text-color-primary);
    }
  }
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-timeline-item__node) {
  background-color: var(--el-color-primary);
}

:deep(.el-timeline-item__timestamp) {
  color: var(--el-text-color-secondary);
}
</style>
