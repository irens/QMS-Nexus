<template>
  <div class="review-reminder-widget">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><AlarmClock /></el-icon>
            文档复审提醒
          </span>
          <el-button type="primary" link @click="goToReviewList">
            查看全部
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>

      <!-- 统计概览 -->
      <div class="stats-overview">
        <div class="stat-item" :class="{ 'has-overdue': stats.overdue_count > 0 }">
          <div class="stat-value">{{ stats.overdue_count }}</div>
          <div class="stat-label">已逾期</div>
        </div>
        <div class="stat-item" :class="{ 'has-urgent': stats.urgent_count > 0 }">
          <div class="stat-value">{{ stats.urgent_count }}</div>
          <div class="stat-label">7天内到期</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.warning_count }}</div>
          <div class="stat-label">30天内到期</div>
        </div>
      </div>

      <!-- 待复审列表 -->
      <div class="pending-list">
        <div v-for="doc in pendingDocuments.slice(0, 5)" :key="doc.id" class="pending-item">
          <div class="item-main">
            <div class="doc-title">
              <el-icon><Document /></el-icon>
              <span :title="doc.document_title">{{ doc.document_title }}</span>
            </div>
            <div class="doc-meta">
              <el-tag size="small">{{ doc.version_label }}</el-tag>
              <el-tag
                size="small"
                :type="getUrgencyType(doc.urgency)"
                effect="dark"
              >
                {{ getUrgencyText(doc.urgency) }}
              </el-tag>
            </div>
          </div>
          <div class="item-sub">
            <span class="review-date">
              复审日期: {{ formatDate(doc.review_date) }}
            </span>
            <span class="days-left" :class="doc.urgency">
              {{ getDaysUntilReviewText(doc.days_until_review) }}
            </span>
          </div>
          <div class="item-actions">
            <el-button
              v-if="doc.urgency === 'overdue' || doc.urgency === 'high'"
              size="small"
              type="danger"
              @click="initiateReview(doc)"
            >
              发起复审
            </el-button>
            <el-button
              v-else
              size="small"
              @click="viewDocument(doc)"
            >
              查看
            </el-button>
          </div>
        </div>

        <el-empty
          v-if="pendingDocuments.length === 0"
          description="暂无待复审文档"
          :image-size="80"
        />
      </div>

      <!-- 进度条 -->
      <div v-if="stats.total_documents > 0" class="review-progress">
        <div class="progress-header">
          <span>复审进度</span>
          <span>{{ Math.round(stats.completion_rate * 100) }}%</span>
        </div>
        <el-progress
          :percentage="Math.round(stats.completion_rate * 100)"
          :status="stats.overdue_count > 0 ? 'exception' : undefined"
        />
      </div>
    </el-card>

    <!-- 发起复审对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="发起文档复审"
      width="600px"
    >
      <div v-if="currentDocument" class="review-dialog-content">
        <el-alert
          :title="`正在为「${currentDocument.document_title}」${currentDocument.version_label} 发起复审`"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />

        <el-form :model="reviewForm" label-width="100px">
          <el-form-item label="复审原因" required>
            <el-input
              v-model="reviewForm.changeSummary"
              type="textarea"
              rows="2"
              placeholder="请简要描述复审原因"
            />
          </el-form-item>
          <el-form-item label="变更详情">
            <el-input
              v-model="reviewForm.changeDetails"
              type="textarea"
              rows="4"
              placeholder="请详细描述变更内容（选填）"
            />
          </el-form-item>
          <el-form-item label="新复审日期">
            <el-date-picker
              v-model="reviewForm.newReviewDate"
              type="date"
              placeholder="选择新的复审日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="reviewLoading"
          @click="confirmInitiateReview"
        >
          确认发起复审
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  AlarmClock,
  ArrowRight,
  Document,
} from '@element-plus/icons-vue';
import reviewReminderService, {
  type PendingReviewDocument,
  type ReviewReminderStats,
} from '@/services/reviewReminder';

const router = useRouter();

// 状态
const loading = ref(false);
const pendingDocuments = ref<PendingReviewDocument[]>([]);
const stats = ref<ReviewReminderStats>({
  total_documents: 0,
  overdue_count: 0,
  urgent_count: 0,
  warning_count: 0,
  normal_count: 0,
  completion_rate: 0,
});

// 复审对话框
const reviewDialogVisible = ref(false);
const reviewLoading = ref(false);
const currentDocument = ref<PendingReviewDocument | null>(null);
const reviewForm = ref({
  changeSummary: '',
  changeDetails: '',
  newReviewDate: '',
});

// 获取数据
async function fetchData() {
  loading.value = true;
  try {
    // 获取待复审文档
    const docsResult = await reviewReminderService.getPendingReviewDocuments({
      page: 1,
      pageSize: 5,
    });
    pendingDocuments.value = docsResult.items;

    // 获取统计
    const statsResult = await reviewReminderService.getReviewReminderStats();
    stats.value = statsResult;
  } catch (error) {
    // 使用模拟数据
    pendingDocuments.value = [
      {
        id: 'doc_001',
        document_id: 'doc_001',
        document_title: '质量管理手册',
        document_code: 'GJZ-QM-01',
        doc_type: '质量手册',
        version_id: 'ver_001',
        version_label: 'V2.0',
        version_number: 2,
        effective_date: '2022-01-15',
        review_date: '2024-01-15',
        days_until_review: -45,
        urgency: 'overdue',
        kb_id: 'default',
      },
      {
        id: 'doc_002',
        document_id: 'doc_002',
        document_title: '记录控制程序',
        document_code: 'GJZ-QP-01',
        doc_type: '程序文件',
        version_id: 'ver_002',
        version_label: 'V3.0',
        version_number: 3,
        effective_date: '2023-02-20',
        review_date: '2024-02-20',
        days_until_review: 3,
        urgency: 'high',
        kb_id: 'default',
      },
      {
        id: 'doc_003',
        document_id: 'doc_003',
        document_title: '设计开发控制程序',
        document_code: 'GJZ-QP-02',
        doc_type: '程序文件',
        version_id: 'ver_003',
        version_label: 'V1.0',
        version_number: 1,
        effective_date: '2023-06-10',
        review_date: '2024-06-10',
        days_until_review: 25,
        urgency: 'medium',
        kb_id: 'default',
      },
    ];
    stats.value = {
      total_documents: 50,
      overdue_count: 1,
      urgent_count: 2,
      warning_count: 5,
      normal_count: 42,
      completion_rate: 0.85,
    };
  } finally {
    loading.value = false;
  }
}

// 跳转到复审列表
function goToReviewList() {
  router.push('/documents?tab=pending-review');
}

// 查看文档
function viewDocument(doc: PendingReviewDocument) {
  router.push(`/documents/${doc.document_id}/versions`);
}

// 发起复审
function initiateReview(doc: PendingReviewDocument) {
  currentDocument.value = doc;
  reviewForm.value = {
    changeSummary: '',
    changeDetails: '',
    newReviewDate: '',
  };
  reviewDialogVisible.value = true;
}

// 确认发起复审
async function confirmInitiateReview() {
  if (!currentDocument.value) return;
  if (!reviewForm.value.changeSummary) {
    ElMessage.warning('请输入复审原因');
    return;
  }

  reviewLoading.value = true;
  try {
    await reviewReminderService.initiateReview(currentDocument.value.document_id, {
      changeSummary: reviewForm.value.changeSummary,
      changeDetails: reviewForm.value.changeDetails || undefined,
      newReviewDate: reviewForm.value.newReviewDate || undefined,
    });
    ElMessage.success('复审发起成功');
    reviewDialogVisible.value = false;
    fetchData();
  } catch (error) {
    ElMessage.error('发起复审失败: ' + (error as Error).message);
  } finally {
    reviewLoading.value = false;
  }
}

// 工具函数
function getUrgencyText(urgency: string): string {
  return reviewReminderService.getUrgencyText(urgency);
}

function getUrgencyType(urgency: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  return reviewReminderService.getUrgencyType(urgency);
}

function formatDate(dateStr?: string): string {
  return reviewReminderService.formatDate(dateStr);
}

function getDaysUntilReviewText(days: number): string {
  return reviewReminderService.getDaysUntilReviewText(days);
}

// 初始化
onMounted(() => {
  fetchData();
});
</script>

<style scoped lang="scss">
.review-reminder-widget {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;

      .el-icon {
        color: var(--el-color-warning);
      }
    }
  }

  .stats-overview {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-light);

    .stat-item {
      flex: 1;
      text-align: center;
      padding: 12px;
      border-radius: 8px;
      background-color: var(--el-fill-color-light);

      &.has-overdue {
        background-color: var(--el-color-danger-light-9);

        .stat-value {
          color: var(--el-color-danger);
        }
      }

      &.has-urgent {
        background-color: var(--el-color-warning-light-9);

        .stat-value {
          color: var(--el-color-warning);
        }
      }

      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        line-height: 1.2;
      }

      .stat-label {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-top: 4px;
      }
    }
  }

  .pending-list {
    .pending-item {
      padding: 12px;
      border-bottom: 1px solid var(--el-border-color-light);
      transition: background-color 0.2s;

      &:last-child {
        border-bottom: none;
      }

      &:hover {
        background-color: var(--el-fill-color-light);
      }

      .item-main {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .doc-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          color: var(--el-text-color-primary);

          .el-icon {
            color: var(--el-color-primary);
          }

          span {
            max-width: 200px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }

        .doc-meta {
          display: flex;
          gap: 8px;
        }
      }

      .item-sub {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13px;
        color: var(--el-text-color-secondary);
        margin-bottom: 8px;

        .days-left {
          &.overdue {
            color: var(--el-color-danger);
            font-weight: 500;
          }

          &.high {
            color: var(--el-color-warning);
            font-weight: 500;
          }
        }
      }

      .item-actions {
        display: flex;
        justify-content: flex-end;
      }
    }
  }

  .review-progress {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-light);

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}

.review-dialog-content {
  .el-form {
    margin-top: 16px;
  }
}
</style>
