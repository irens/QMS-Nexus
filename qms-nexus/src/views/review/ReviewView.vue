<template>
  <div class="review-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>审批中心</span>
          <el-radio-group v-model="activeTab" size="small">
            <el-radio-button label="pending">
              待审批
              <el-badge v-if="pendingCount > 0" :value="pendingCount" class="tab-badge" />
            </el-radio-button>
            <el-radio-button label="history">审批历史</el-radio-button>
            <el-radio-button label="submissions">我的提交</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 待审批列表 -->
      <div v-if="activeTab === 'pending'" class="tab-content">
        <div class="toolbar">
          <el-input
            v-model="pendingSearchQuery"
            placeholder="搜索文档名称..."
            clearable
            style="width: 300px"
            @keyup.enter="fetchPendingReviews"
          >
            <template #append>
              <el-button @click="fetchPendingReviews">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-button type="primary" @click="fetchPendingReviews">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-table
          v-loading="pendingLoading"
          :data="pendingReviews"
          style="width: 100%"
          @row-click="handlePendingRowClick"
        >
          <el-table-column type="index" width="50" />
          <el-table-column label="文档名称" min-width="200">
            <template #default="{ row }">
              <div class="doc-name">
                <el-icon class="doc-icon"><Document /></el-icon>
                <div class="doc-info">
                  <span class="doc-title">{{ row.document_title }}</span>
                  <span v-if="row.document_code" class="doc-code">{{ row.document_code }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="版本" width="100">
            <template #default="{ row }">
              <el-tag size="small" type="warning">{{ row.version_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="变更摘要" min-width="200">
            <template #default="{ row }">
              <el-tooltip :content="row.change_summary" placement="top">
                <span class="ellipsis">{{ row.change_summary }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="提交人" width="120">
            <template #default="{ row }">
              {{ row.submitted_by }}
            </template>
          </el-table-column>
          <el-table-column label="提交时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.submitted_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                size="small"
                type="success"
                @click.stop="handleApprove(row)"
              >
                <el-icon><Check /></el-icon>
                通过
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click.stop="handleReject(row)"
              >
                <el-icon><Close /></el-icon>
                拒绝
              </el-button>
              <el-button
                size="small"
                @click.stop="viewDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pendingPage"
            v-model:page-size="pendingPageSize"
            :total="pendingTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchPendingReviews"
            @current-change="fetchPendingReviews"
          />
        </div>
      </div>

      <!-- 审批历史 -->
      <div v-else-if="activeTab === 'history'" class="tab-content">
        <div class="toolbar">
          <el-input
            v-model="historySearchQuery"
            placeholder="搜索文档名称..."
            clearable
            style="width: 300px"
            @keyup.enter="fetchReviewHistory"
          >
            <template #append>
              <el-button @click="fetchReviewHistory">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-button type="primary" @click="fetchReviewHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-timeline>
          <el-timeline-item
            v-for="item in reviewHistory"
            :key="item.id"
            :type="getTimelineType(item.action)"
            :timestamp="formatDateTime(item.action_at)"
          >
            <el-card class="history-card">
              <div class="history-content">
                <div class="history-header">
                  <span class="doc-title">{{ item.document_title }}</span>
                  <el-tag
                    size="small"
                    :type="item.action === 'approve' ? 'success' : 'danger'"
                  >
                    {{ item.action === 'approve' ? '通过' : '拒绝' }}
                  </el-tag>
                </div>
                <div class="history-meta">
                  <span>版本: {{ item.version_label }}</span>
                  <span>审批人: {{ item.action_by }}</span>
                </div>
                <div v-if="item.comment" class="history-comment">
                  <el-icon><ChatDotRound /></el-icon>
                  {{ item.comment }}
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>

        <el-empty v-if="reviewHistory.length === 0 && !historyLoading" description="暂无审批记录" />

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="historyPage"
            v-model:page-size="historyPageSize"
            :total="historyTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchReviewHistory"
            @current-change="fetchReviewHistory"
          />
        </div>
      </div>

      <!-- 我的提交 -->
      <div v-else-if="activeTab === 'submissions'" class="tab-content">
        <div class="toolbar">
          <el-input
            v-model="submissionSearchQuery"
            placeholder="搜索文档名称..."
            clearable
            style="width: 300px"
            @keyup.enter="fetchMySubmissions"
          >
            <template #append>
              <el-button @click="fetchMySubmissions">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-select
            v-model="submissionStatusFilter"
            placeholder="状态筛选"
            clearable
            style="width: 150px; margin-left: 10px"
            @change="fetchMySubmissions"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="审核中" value="review" />
            <el-option label="已批准" value="approved" />
            <el-option label="生效中" value="effective" />
            <el-option label="已作废" value="obsolete" />
          </el-select>
          <el-button type="primary" @click="fetchMySubmissions">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>

        <el-table
          v-loading="submissionLoading"
          :data="mySubmissions"
          style="width: 100%"
        >
          <el-table-column type="index" width="50" />
          <el-table-column label="文档名称" min-width="200">
            <template #default="{ row }">
              <div class="doc-name">
                <el-icon class="doc-icon"><Document /></el-icon>
                <div class="doc-info">
                  <span class="doc-title">{{ row.document_title }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="版本" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.version_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="提交时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.submitted_at) }}
            </template>
          </el-table-column>
          <el-table-column label="审批信息" min-width="200">
            <template #default="{ row }">
              <div v-if="row.reviewed_by">
                <span>审批人: {{ row.reviewed_by }}</span>
                <br />
                <span>审批时间: {{ formatDateTime(row.reviewed_at) }}</span>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'draft'"
                size="small"
                type="primary"
                @click="editSubmission(row)"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                @click="viewSubmissionDetail(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="submissionPage"
            v-model:page-size="submissionPageSize"
            :total="submissionTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="fetchMySubmissions"
            @current-change="fetchMySubmissions"
          />
        </div>
      </div>
    </el-card>

    <!-- 审批详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="审批详情"
      width="800px"
      destroy-on-close
    >
      <div v-if="currentReviewDetail" class="review-detail">
        <!-- 文档信息 -->
        <el-descriptions title="文档信息" :column="2" border>
          <el-descriptions-item label="文档名称">
            {{ currentReviewDetail.document.title }}
          </el-descriptions-item>
          <el-descriptions-item label="文档编号">
            {{ currentReviewDetail.document.doc_code || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="文档类型">
            {{ currentReviewDetail.document.doc_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            <el-tag type="warning">{{ currentReviewDetail.version.version_label }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件名">
            {{ currentReviewDetail.version.filename }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(currentReviewDetail.version.file_size) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 变更信息 -->
        <el-descriptions title="变更信息" :column="1" border style="margin-top: 20px">
          <el-descriptions-item label="变更摘要">
            {{ currentReviewDetail.version.change_summary }}
          </el-descriptions-item>
          <el-descriptions-item label="变更详情">
            {{ currentReviewDetail.version.change_details || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 版本对比 -->
        <div v-if="currentReviewDetail.previous_version" class="version-compare-section">
          <h4>版本对比</h4>
          <el-alert
            :title="`对比版本: ${currentReviewDetail.previous_version.version_label} → ${currentReviewDetail.version.version_label}`"
            type="info"
            :closable="false"
          />
          <div class="compare-actions">
            <el-button type="primary" @click="viewVersionCompare">
              <el-icon><View /></el-icon>
              查看详细对比
            </el-button>
          </div>
        </div>

        <!-- 审批历史 -->
        <div class="approval-history-section">
          <h4>审批历史</h4>
          <el-timeline>
            <el-timeline-item
              v-for="history in currentReviewDetail.approval_history"
              :key="history.id"
              :type="getTimelineType(history.action)"
              :timestamp="formatDateTime(history.action_at)"
            >
              <div class="history-item">
                <span class="action">{{ getActionText(history.action) }}</span>
                <span class="operator">{{ history.action_by }}</span>
                <p v-if="history.comment" class="comment">{{ history.comment }}</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button
          v-if="activeTab === 'pending'"
          type="danger"
          @click="handleDetailReject"
        >
          拒绝
        </el-button>
        <el-button
          v-if="activeTab === 'pending'"
          type="success"
          @click="handleDetailApprove"
        >
          通过
        </el-button>
      </template>
    </el-dialog>

    <!-- 审批操作对话框 -->
    <el-dialog
      v-model="actionDialogVisible"
      :title="actionType === 'approve' ? '审批通过' : '审批拒绝'"
      width="500px"
    >
      <el-form :model="actionForm" label-width="80px">
        <el-form-item label="审批意见">
          <el-input
            v-model="actionForm.comment"
            type="textarea"
            rows="4"
            :placeholder="actionType === 'approve' ? '请输入审批意见（选填）' : '请输入拒绝原因（必填）'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button
          :type="actionType === 'approve' ? 'success' : 'danger'"
          :loading="actionLoading"
          @click="confirmAction"
        >
          {{ actionType === 'approve' ? '确认通过' : '确认拒绝' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Search,
  Refresh,
  Document,
  Check,
  Close,
  ChatDotRound,
  View,
} from '@element-plus/icons-vue';
import approvalWorkflowService, {
  type PendingReviewItem,
  type ReviewHistoryItem,
  type MySubmissionItem,
  type ReviewDetail,
} from '@/services/approvalWorkflow';
import documentVersionService from '@/services/documentVersion';

const router = useRouter();

// 标签页
const activeTab = ref<'pending' | 'history' | 'submissions'>('pending');

// 待审批列表
const pendingReviews = ref<PendingReviewItem[]>([]);
const pendingLoading = ref(false);
const pendingPage = ref(1);
const pendingPageSize = ref(10);
const pendingTotal = ref(0);
const pendingSearchQuery = ref('');
const pendingCount = computed(() => pendingTotal.value);

// 审批历史
const reviewHistory = ref<ReviewHistoryItem[]>([]);
const historyLoading = ref(false);
const historyPage = ref(1);
const historyPageSize = ref(10);
const historyTotal = ref(0);
const historySearchQuery = ref('');

// 我的提交
const mySubmissions = ref<MySubmissionItem[]>([]);
const submissionLoading = ref(false);
const submissionPage = ref(1);
const submissionPageSize = ref(10);
const submissionTotal = ref(0);
const submissionSearchQuery = ref('');
const submissionStatusFilter = ref('');

// 详情对话框
const detailDialogVisible = ref(false);
const currentReviewDetail = ref<ReviewDetail | null>(null);
const currentVersionId = ref('');

// 操作对话框
const actionDialogVisible = ref(false);
const actionType = ref<'approve' | 'reject'>('approve');
const actionLoading = ref(false);
const actionForm = ref({
  comment: '',
});

// 获取待审批列表
async function fetchPendingReviews() {
  pendingLoading.value = true;
  try {
    const result = await approvalWorkflowService.getPendingReviews({
      page: pendingPage.value,
      pageSize: pendingPageSize.value,
    });
    pendingReviews.value = result.items;
    pendingTotal.value = result.total;
  } catch (error) {
    ElMessage.error('获取待审批列表失败: ' + (error as Error).message);
    // 使用模拟数据
    pendingReviews.value = [
      {
        id: 'review_001',
        version_id: 'ver_002',
        document_id: 'doc_002',
        document_title: '记录控制程序',
        document_code: 'GJZ-QP-01',
        filename: '记录控制程序.docx',
        version_number: 3,
        version_label: 'V3.0',
        change_summary: '更新记录保存期限要求，从3年改为5年',
        change_details: '根据新法规要求，所有质量记录保存期限从3年延长至5年',
        submitted_by: '张三',
        submitted_at: '2024-02-20T10:00:00',
        previous_version_id: 'ver_001',
        previous_version_label: 'V2.1',
      },
    ];
    pendingTotal.value = pendingReviews.value.length;
  } finally {
    pendingLoading.value = false;
  }
}

// 获取审批历史
async function fetchReviewHistory() {
  historyLoading.value = true;
  try {
    const result = await approvalWorkflowService.getReviewHistory({
      page: historyPage.value,
      pageSize: historyPageSize.value,
    });
    reviewHistory.value = result.items;
    historyTotal.value = result.total;
  } catch (error) {
    ElMessage.error('获取审批历史失败: ' + (error as Error).message);
  } finally {
    historyLoading.value = false;
  }
}

// 获取我的提交
async function fetchMySubmissions() {
  submissionLoading.value = true;
  try {
    const result = await approvalWorkflowService.getMySubmissions({
      page: submissionPage.value,
      pageSize: submissionPageSize.value,
    });
    mySubmissions.value = result.items;
    submissionTotal.value = result.total;
  } catch (error) {
    ElMessage.error('获取我的提交失败: ' + (error as Error).message);
    // 使用模拟数据
    mySubmissions.value = [
      {
        id: 'sub_001',
        version_id: 'ver_003',
        document_id: 'doc_003',
        document_title: '设计开发控制程序',
        version_label: 'V1.0',
        status: 'review',
        submitted_at: '2024-02-18T09:00:00',
      },
      {
        id: 'sub_002',
        version_id: 'ver_004',
        document_id: 'doc_004',
        document_title: '采购控制程序',
        version_label: 'V2.0',
        status: 'effective',
        submitted_at: '2024-02-10T14:00:00',
        reviewed_by: '李四',
        reviewed_at: '2024-02-12T10:00:00',
      },
    ];
    submissionTotal.value = mySubmissions.value.length;
  } finally {
    submissionLoading.value = false;
  }
}

// 查看详情
async function viewDetail(row: PendingReviewItem) {
  currentVersionId.value = row.version_id;
  try {
    const detail = await approvalWorkflowService.getReviewDetail(row.version_id);
    currentReviewDetail.value = detail;
    detailDialogVisible.value = true;
  } catch (error) {
    ElMessage.error('获取审批详情失败: ' + (error as Error).message);
  }
}

// 处理行点击
function handlePendingRowClick(row: PendingReviewItem) {
  viewDetail(row);
}

// 处理通过
function handleApprove(row: PendingReviewItem) {
  currentVersionId.value = row.version_id;
  actionType.value = 'approve';
  actionForm.value.comment = '';
  actionDialogVisible.value = true;
}

// 处理拒绝
function handleReject(row: PendingReviewItem) {
  currentVersionId.value = row.version_id;
  actionType.value = 'reject';
  actionForm.value.comment = '';
  actionDialogVisible.value = true;
}

// 确认操作
async function confirmAction() {
  if (actionType.value === 'reject' && !actionForm.value.comment) {
    ElMessage.warning('请输入拒绝原因');
    return;
  }

  actionLoading.value = true;
  try {
    if (actionType.value === 'approve') {
      await approvalWorkflowService.approveVersion(currentVersionId.value, {
        comment: actionForm.value.comment,
      });
      ElMessage.success('审批通过成功');
    } else {
      await approvalWorkflowService.rejectVersion(currentVersionId.value, {
        comment: actionForm.value.comment,
      });
      ElMessage.success('已拒绝该版本');
    }

    actionDialogVisible.value = false;
    detailDialogVisible.value = false;
    fetchPendingReviews();
    fetchReviewHistory();
  } catch (error) {
    ElMessage.error('操作失败: ' + (error as Error).message);
  } finally {
    actionLoading.value = false;
  }
}

// 详情页操作
function handleDetailApprove() {
  actionType.value = 'approve';
  actionForm.value.comment = '';
  actionDialogVisible.value = true;
}

function handleDetailReject() {
  actionType.value = 'reject';
  actionForm.value.comment = '';
  actionDialogVisible.value = true;
}

// 查看版本对比
function viewVersionCompare() {
  if (currentReviewDetail.value?.previous_version) {
    router.push({
      path: '/documents/compare',
      query: {
        v1: currentReviewDetail.value.previous_version.id,
        v2: currentReviewDetail.value.version.id,
      },
    });
  }
}

// 编辑提交
function editSubmission(row: MySubmissionItem) {
  router.push(`/documents/versions/${row.version_id}`);
}

// 查看提交详情
function viewSubmissionDetail(row: MySubmissionItem) {
  router.push(`/documents/versions/${row.version_id}`);
}

// 工具函数
function formatDateTime(dateStr?: string): string {
  return approvalWorkflowService.formatDateTime(dateStr);
}

function formatFileSize(bytes: number): string {
  return documentVersionService.formatFileSize(bytes);
}

function getStatusText(status: string): string {
  return documentVersionService.getStatusText(status as any);
}

function getStatusType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  return documentVersionService.getStatusType(status as any);
}

function getActionText(action: string): string {
  return approvalWorkflowService.getActionText(action);
}

function getTimelineType(action: string): '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  return documentVersionService.getTimelineItemType(action as any);
}

// 初始化
onMounted(() => {
  fetchPendingReviews();
  fetchReviewHistory();
  fetchMySubmissions();
});
</script>

<style scoped lang="scss">
.review-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-badge {
  margin-left: 4px;

  :deep(.el-badge__content) {
    position: relative;
    top: -1px;
  }
}

.tab-content {
  min-height: 400px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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

.ellipsis {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

// 历史记录样式
.history-card {
  margin-bottom: 10px;
}

.history-content {
  .history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;

    .doc-title {
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }

  .history-meta {
    display: flex;
    gap: 20px;
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-bottom: 10px;
  }

  .history-comment {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 10px;
    background-color: var(--el-fill-color-light);
    border-radius: 4px;
    font-size: 13px;
    color: var(--el-text-color-regular);

    .el-icon {
      margin-top: 2px;
      flex-shrink: 0;
    }
  }
}

// 审批详情样式
.review-detail {
  max-height: 600px;
  overflow-y: auto;
}

.version-compare-section {
  margin-top: 20px;

  h4 {
    margin-bottom: 10px;
    color: var(--el-text-color-primary);
  }

  .compare-actions {
    margin-top: 10px;
  }
}

.approval-history-section {
  margin-top: 20px;

  h4 {
    margin-bottom: 10px;
    color: var(--el-text-color-primary);
  }
}

.history-item {
  .action {
    font-weight: 500;
    margin-right: 10px;
  }

  .operator {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }

  .comment {
    margin-top: 8px;
    padding: 8px;
    background-color: var(--el-fill-color-light);
    border-radius: 4px;
    font-size: 13px;
    color: var(--el-text-color-regular);
  }
}

:deep(.el-timeline-item__node) {
  background-color: var(--el-color-primary);
}

:deep(.el-timeline-item__timestamp) {
  color: var(--el-text-color-secondary);
}
</style>
