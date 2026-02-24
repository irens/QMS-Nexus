<template>
  <div class="version-detail">
    <el-page-header @back="goBack" :content="pageTitle" />
    
    <div v-loading="loading" class="content-wrapper">
      <template v-if="versionDetail">
        <!-- 版本基本信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>版本信息</span>
              <div class="header-actions">
                <el-tag :type="getStatusType(version.status)" size="large">
                  {{ getStatusText(version.status) }}
                </el-tag>
                <el-tag v-if="version.is_latest" type="success" size="large" effect="dark">
                  最新版本
                </el-tag>
              </div>
            </div>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="版本号">
              {{ version.version_label || `V${version.version_number}` }}
            </el-descriptions-item>
            <el-descriptions-item label="文件名">
              {{ version.filename }}
            </el-descriptions-item>
            <el-descriptions-item label="文档标题">
              {{ version.title || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="文档编号">
              {{ version.doc_code || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="文档类型">
              {{ version.doc_type || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ formatFileSize(version.file_size) }}
            </el-descriptions-item>
            <el-descriptions-item label="文件类型">
              {{ version.file_type }}
            </el-descriptions-item>
            <el-descriptions-item label="知识库">
              {{ version.kb_id }}
            </el-descriptions-item>
            <el-descriptions-item label="编制人">
              {{ version.prepared_by || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="审核人">
              {{ version.reviewed_by || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="批准人">
              {{ version.approved_by || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="批准日期">
              {{ formatDate(version.approved_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="生效日期">
              {{ formatDate(version.effective_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="复审日期">
              {{ formatDate(version.review_date) }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(version.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDateTime(version.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="description-section" v-if="version.description">
            <h4>文档描述</h4>
            <p>{{ version.description }}</p>
          </div>

          <div class="change-section" v-if="version.change_summary">
            <h4>变更摘要</h4>
            <p>{{ version.change_summary }}</p>
          </div>

          <div class="change-section" v-if="version.change_details">
            <h4>变更详情</h4>
            <p>{{ version.change_details }}</p>
          </div>

          <div class="action-buttons">
            <el-button type="primary" @click="downloadVersion" :icon="Download">
              下载文件
            </el-button>
            <el-button 
              v-if="previousVersion" 
              @click="compareWithPrevious"
              :icon="Switch"
            >
              对比上一版本
            </el-button>
            <el-button 
              v-if="canSubmitForReview" 
              type="warning" 
              @click="submitForReview"
            >
              提交审核
            </el-button>
            <el-button 
              v-if="canApprove" 
              type="success" 
              @click="approveVersion"
            >
              审批通过
            </el-button>
            <el-button 
              v-if="canReject" 
              type="danger" 
              @click="rejectVersion"
            >
              拒绝
            </el-button>
            <el-button 
              v-if="canObsolete" 
              type="danger" 
              plain
              @click="obsoleteVersion"
            >
              作废版本
            </el-button>
          </div>
        </el-card>

        <!-- 上一版本信息 -->
        <el-card v-if="previousVersion" class="previous-version-card">
          <template #header>
            <span>上一版本信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="版本号">
              {{ previousVersion.version_label || `V${previousVersion.version_number}` }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(previousVersion.status)" size="small">
                {{ getStatusText(previousVersion.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="文件名">
              {{ previousVersion.filename }}
            </el-descriptions-item>
            <el-descriptions-item label="生效日期">
              {{ formatDate(previousVersion.effective_date) }}
            </el-descriptions-item>
          </el-descriptions>
          <div class="previous-actions">
            <el-button size="small" @click="viewPreviousVersion">
              查看上一版本详情
            </el-button>
          </div>
        </el-card>

        <!-- 审批历史 -->
        <el-card class="approval-history-card">
          <template #header>
            <span>审批历史</span>
          </template>
          
          <el-timeline v-if="approvalHistory.length > 0">
            <el-timeline-item
              v-for="(history, index) in approvalHistory"
              :key="history.id"
              :type="getHistoryType(history.action)"
              :timestamp="formatDateTime(history.action_at)"
            >
              <el-card class="history-card">
                <div class="history-header">
                  <span class="action-text">{{ getActionText(history.action) }}</span>
                  <el-tag size="small" :type="getStatusTransitionType(history.from_status, history.to_status)">
                    {{ history.from_status || '无' }} → {{ history.to_status }}
                  </el-tag>
                </div>
                <div class="history-info">
                  <p><strong>操作人：</strong>{{ history.action_by }}</p>
                  <p v-if="history.comment"><strong>意见：</strong>{{ history.comment }}</p>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          
          <el-empty v-else description="暂无审批记录" />
        </el-card>
      </template>

      <el-empty v-else-if="!loading" description="版本不存在或已被删除" />
    </div>

    <!-- 审批对话框 -->
    <el-dialog
      v-model="approveDialogVisible"
      :title="approvalAction === 'approve' ? '审批通过' : '审批拒绝'"
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
import { Download, Switch } from '@element-plus/icons-vue';
import documentVersionService, { 
  Version, 
  VersionDetail, 
  ApprovalHistory, 
  VersionStatus 
} from '@/services/documentVersion';

const route = useRoute();
const router = useRouter();

// 版本ID
const versionId = computed(() => route.params.versionId as string);

// 数据
const versionDetail = ref<VersionDetail | null>(null);
const loading = ref(false);

// 计算属性
const version = computed(() => versionDetail.value?.version);
const previousVersion = computed(() => versionDetail.value?.previous_version);
const approvalHistory = computed(() => versionDetail.value?.approval_history || []);
const pageTitle = computed(() => {
  if (!version.value) return '版本详情';
  return `版本详情 - ${version.value.version_label || `V${version.value.version_number}`}`;
});

// 权限判断
const canSubmitForReview = computed(() => version.value?.status === 'draft');
const canApprove = computed(() => {
  if (!version.value) return false;
  return version.value.status === 'review' || version.value.status === 'approved';
});
const canReject = computed(() => version.value?.status === 'review');
const canObsolete = computed(() => {
  if (!version.value) return false;
  return version.value.status === 'effective' || version.value.status === 'approved';
});

// 审批对话框
const approveDialogVisible = ref(false);
const approvalLoading = ref(false);
const approvalComment = ref('');
const approvalAction = ref<'approve' | 'reject'>('approve');

// 作废对话框
const obsoleteDialogVisible = ref(false);
const obsoleteLoading = ref(false);
const obsoleteReason = ref('');

// 获取版本详情
const fetchVersionDetail = async () => {
  if (!versionId.value) return;
  
  loading.value = true;
  try {
    versionDetail.value = await documentVersionService.getVersionDetail(versionId.value);
  } catch (error) {
    ElMessage.error('获取版本详情失败：' + (error as Error).message);
  } finally {
    loading.value = false;
  }
};

// 返回上一页
const goBack = () => {
  router.back();
};

// 下载版本
const downloadVersion = async () => {
  if (!version.value) return;
  
  try {
    const blob = await documentVersionService.downloadVersion(version.value.id);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = version.value.filename;
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
const compareWithPrevious = () => {
  if (version.value?.previous_version_id) {
    router.push({
      path: '/documents/compare',
      query: {
        v1: version.value.previous_version_id,
        v2: version.value.id,
      },
    });
  }
};

// 查看上一版本详情
const viewPreviousVersion = () => {
  if (previousVersion.value) {
    router.push(`/documents/versions/${previousVersion.value.id}`);
  }
};

// 提交审核
const submitForReview = async () => {
  if (!version.value) return;
  
  try {
    await ElMessageBox.confirm('确定要提交该版本进行审核吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    await documentVersionService.submitForReview(version.value.id);
    ElMessage.success('提交审核成功');
    fetchVersionDetail();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交审核失败：' + (error as Error).message);
    }
  }
};

// 审批通过
const approveVersion = () => {
  approvalAction.value = 'approve';
  approvalComment.value = '';
  approveDialogVisible.value = true;
};

// 拒绝版本
const rejectVersion = () => {
  approvalAction.value = 'reject';
  approvalComment.value = '';
  approveDialogVisible.value = true;
};

// 确认审批
const confirmApproval = async () => {
  if (!version.value) return;
  
  if (approvalAction.value === 'reject' && !approvalComment.value.trim()) {
    ElMessage.warning('请输入拒绝原因');
    return;
  }
  
  approvalLoading.value = true;
  try {
    if (approvalAction.value === 'approve') {
      await documentVersionService.approveVersion(version.value.id, approvalComment.value);
      ElMessage.success('审批通过');
    } else {
      await documentVersionService.rejectVersion(version.value.id, approvalComment.value);
      ElMessage.success('已拒绝该版本');
    }
    approveDialogVisible.value = false;
    fetchVersionDetail();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    approvalLoading.value = false;
  }
};

// 作废版本
const obsoleteVersion = () => {
  obsoleteReason.value = '';
  obsoleteDialogVisible.value = true;
};

// 确认作废
const confirmObsolete = async () => {
  if (!version.value) return;
  
  obsoleteLoading.value = true;
  try {
    await documentVersionService.obsoleteVersion(version.value.id, obsoleteReason.value);
    ElMessage.success('版本已作废');
    obsoleteDialogVisible.value = false;
    fetchVersionDetail();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    obsoleteLoading.value = false;
  }
};

// 工具函数
const getStatusText = (status: VersionStatus) => documentVersionService.getStatusText(status);
const getStatusType = (status: VersionStatus) => documentVersionService.getStatusType(status);
const formatDate = (date?: string) => documentVersionService.formatDate(date);
const formatDateTime = (date?: string) => documentVersionService.formatDateTime(date);
const formatFileSize = (bytes: number) => documentVersionService.formatFileSize(bytes);

// 获取操作文本
const getActionText = (action: string): string => {
  const actionMap: Record<string, string> = {
    'submit': '提交审核',
    'review': '审核',
    'approve': '批准',
    'reject': '拒绝',
    'publish': '发布',
    'obsolete': '作废',
    'create': '创建',
  };
  return actionMap[action] || action;
};

// 获取历史记录类型
const getHistoryType = (action: string): '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  const typeMap: Record<string, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    'submit': 'primary',
    'review': 'warning',
    'approve': 'success',
    'reject': 'danger',
    'publish': 'success',
    'obsolete': 'danger',
    'create': 'info',
  };
  return typeMap[action] || '';
};

// 获取状态转换类型
const getStatusTransitionType = (from: string | undefined, to: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  if (to === 'effective') return 'success';
  if (to === 'obsolete') return 'danger';
  if (to === 'draft' && from === 'review') return 'warning';
  if (to === 'review') return 'primary';
  return '';
};

onMounted(() => {
  fetchVersionDetail();
});
</script>

<style scoped lang="scss">
.version-detail {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.content-wrapper {
  margin-top: 20px;
}

.info-card,
.previous-version-card,
.approval-history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.description-section,
.change-section {
  margin-top: 20px;
  padding: 15px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;

  h4 {
    margin: 0 0 10px 0;
    color: var(--el-text-color-primary);
  }

  p {
    margin: 0;
    color: var(--el-text-color-regular);
    line-height: 1.6;
    white-space: pre-wrap;
  }
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.previous-actions {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.history-card {
  margin-bottom: 10px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.action-text {
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.history-info {
  p {
    margin: 5px 0;
    color: var(--el-text-color-regular);

    strong {
      color: var(--el-text-color-primary);
    }
  }
}

:deep(.el-descriptions__label) {
  width: 120px;
  background-color: var(--el-fill-color-light);
}

:deep(.el-timeline-item__node) {
  background-color: var(--el-color-primary);
}
</style>
