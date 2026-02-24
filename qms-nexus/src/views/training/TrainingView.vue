<template>
  <div class="training-view">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon pending">
              <el-icon :size="32"><Bell /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pending_tasks }}</div>
              <div class="stat-label">待完成培训</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon completed">
              <el-icon :size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completed_tasks }}</div>
              <div class="stat-label">已完成培训</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_tasks }}</div>
              <div class="stat-label">培训任务总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon rate">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ Math.round(stats.completion_rate * 100) }}%</div>
              <div class="stat-label">完成率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 培训任务列表 -->
    <el-card class="task-list-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>培训任务</span>
          <div class="header-actions">
            <el-radio-group v-model="taskFilter" size="small" @change="fetchTasks">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="pending">
                待完成
                <el-badge v-if="pendingCount > 0" :value="pendingCount" class="filter-badge" />
              </el-radio-button>
              <el-radio-button label="completed">已完成</el-radio-button>
            </el-radio-group>
            <el-button type="primary" size="small" @click="fetchTasks">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="filteredTasks"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column type="index" width="50" />
        <el-table-column label="文档名称" min-width="250">
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
            <el-tag size="small" type="success">{{ row.version_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="培训类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getDistributionTypeTag(row.distribution_type)">
              {{ getDistributionTypeText(row.distribution_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变更摘要" min-width="200">
          <template #default="{ row }">
            <el-tooltip v-if="row.change_summary" :content="row.change_summary" placement="top">
              <span class="ellipsis">{{ row.change_summary }}</span>
            </el-tooltip>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="生效日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.effective_date) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分发时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.distributed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="完成时间" width="160">
          <template #default="{ row }">
            {{ row.completed_at ? formatDateTime(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="primary"
              @click.stop="handleAcknowledge(row)"
            >
              <el-icon><Check /></el-icon>
              确认完成
            </el-button>
            <el-button
              v-else
              size="small"
              @click.stop="viewDocument(row)"
            >
              查看文档
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchTasks"
          @current-change="fetchTasks"
        />
      </div>
    </el-card>

    <!-- 最近完成记录 -->
    <el-card v-if="stats.recent_completions?.length > 0" class="recent-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>最近完成</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="item in stats.recent_completions"
          :key="item.document_title + item.completed_at"
          type="success"
          :timestamp="formatDateTime(item.completed_at)"
        >
          <span class="doc-title">{{ item.document_title }}</span>
          <el-tag size="small" style="margin-left: 8px;">{{ item.version_label }}</el-tag>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 确认对话框 -->
    <el-dialog
      v-model="acknowledgeDialogVisible"
      title="确认培训完成"
      width="500px"
    >
      <div class="acknowledge-content">
        <el-alert
          title="请确认您已完成以下培训内容"
          type="info"
          :closable="false"
          show-icon
        />
        <div v-if="currentTask" class="task-info">
          <p><strong>文档:</strong> {{ currentTask.document_title }}</p>
          <p><strong>版本:</strong> {{ currentTask.version_label }}</p>
          <p><strong>培训类型:</strong> {{ getDistributionTypeText(currentTask.distribution_type) }}</p>
          <p v-if="currentTask.change_summary"><strong>变更内容:</strong> {{ currentTask.change_summary }}</p>
        </div>
        <el-checkbox v-model="acknowledgeConfirmed">
          我已阅读并理解上述文档的变更内容
        </el-checkbox>
      </div>
      <template #footer>
        <el-button @click="acknowledgeDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="!acknowledgeConfirmed"
          :loading="acknowledgeLoading"
          @click="confirmAcknowledge"
        >
          确认完成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  Bell,
  CircleCheck,
  Document,
  TrendCharts,
  Refresh,
  Check,
} from '@element-plus/icons-vue';
import trainingService, {
  type TrainingTask,
  type TrainingStats,
} from '@/services/training';

const router = useRouter();

// 状态
const loading = ref(false);
const tasks = ref<TrainingTask[]>([]);
const page = ref(1);
const pageSize = ref(10);
const total = ref(0);
const taskFilter = ref<'all' | 'pending' | 'completed'>('all');
const pendingCount = ref(0);

// 统计
const stats = ref<TrainingStats>({
  total_tasks: 0,
  pending_tasks: 0,
  completed_tasks: 0,
  completion_rate: 0,
  recent_completions: [],
});

// 确认对话框
const acknowledgeDialogVisible = ref(false);
const acknowledgeLoading = ref(false);
const acknowledgeConfirmed = ref(false);
const currentTask = ref<TrainingTask | null>(null);

// 过滤后的任务列表
const filteredTasks = computed(() => {
  if (taskFilter.value === 'all') return tasks.value;
  return tasks.value.filter(task => task.status === taskFilter.value);
});

// 获取培训任务列表
async function fetchTasks() {
  loading.value = true;
  try {
    const status = taskFilter.value === 'all' ? undefined : taskFilter.value;
    const result = await trainingService.getMyTrainingTasks({
      status,
      page: page.value,
      pageSize: pageSize.value,
    });
    tasks.value = result.items;
    total.value = result.total;
    pendingCount.value = result.pending_count;
  } catch (error) {
    ElMessage.error('获取培训任务失败: ' + (error as Error).message);
    // 使用模拟数据
    tasks.value = [
      {
        id: 'task_001',
        document_version_id: 'ver_001',
        document_id: 'doc_001',
        document_title: '质量管理手册',
        document_code: 'GJZ-QM-01',
        version_label: 'V2.0',
        version_number: 2,
        distribution_type: 'read',
        status: 'pending',
        distributed_at: '2024-02-20T10:00:00',
        effective_date: '2024-02-20',
        change_summary: '更新质量方针和目标',
      },
      {
        id: 'task_002',
        document_version_id: 'ver_002',
        document_id: 'doc_002',
        document_title: '记录控制程序',
        document_code: 'GJZ-QP-01',
        version_label: 'V3.0',
        version_number: 3,
        distribution_type: 'training',
        status: 'pending',
        distributed_at: '2024-02-18T09:00:00',
        effective_date: '2024-02-18',
        change_summary: '记录保存期限从3年改为5年',
      },
      {
        id: 'task_003',
        document_version_id: 'ver_003',
        document_id: 'doc_003',
        document_title: '设计开发控制程序',
        version_label: 'V1.0',
        version_number: 1,
        distribution_type: 'acknowledge',
        status: 'completed',
        distributed_at: '2024-02-10T14:00:00',
        completed_at: '2024-02-12T10:00:00',
        effective_date: '2024-02-10',
      },
    ];
    total.value = tasks.value.length;
    pendingCount.value = tasks.value.filter(t => t.status === 'pending').length;
  } finally {
    loading.value = false;
  }
}

// 获取培训统计
async function fetchStats() {
  try {
    const result = await trainingService.getTrainingStats();
    stats.value = result;
  } catch (error) {
    // 使用模拟数据
    stats.value = {
      total_tasks: 10,
      pending_tasks: 3,
      completed_tasks: 7,
      completion_rate: 0.7,
      recent_completions: [
        {
          document_title: '设计开发控制程序',
          version_label: 'V1.0',
          completed_at: '2024-02-12T10:00:00',
        },
        {
          document_title: '采购控制程序',
          version_label: 'V2.0',
          completed_at: '2024-02-10T14:00:00',
        },
      ],
    };
  }
}

// 处理行点击
function handleRowClick(row: TrainingTask) {
  viewDocument(row);
}

// 处理确认完成
function handleAcknowledge(row: TrainingTask) {
  currentTask.value = row;
  acknowledgeConfirmed.value = false;
  acknowledgeDialogVisible.value = true;
}

// 确认完成
async function confirmAcknowledge() {
  if (!currentTask.value) return;

  acknowledgeLoading.value = true;
  try {
    await trainingService.acknowledgeTraining(currentTask.value.id);
    ElMessage.success('培训确认完成');
    acknowledgeDialogVisible.value = false;
    fetchTasks();
    fetchStats();
  } catch (error) {
    ElMessage.error('确认失败: ' + (error as Error).message);
  } finally {
    acknowledgeLoading.value = false;
  }
}

// 查看文档
function viewDocument(row: TrainingTask) {
  router.push(`/documents/versions/${row.document_version_id}`);
}

// 工具函数
function getDistributionTypeText(type: string): string {
  return trainingService.getDistributionTypeText(type);
}

function getDistributionTypeTag(type: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  return trainingService.getDistributionTypeTag(type);
}

function getStatusText(status: string): string {
  return trainingService.getStatusText(status);
}

function getStatusType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  return trainingService.getStatusType(status);
}

function formatDateTime(dateStr?: string): string {
  return trainingService.formatDateTime(dateStr);
}

function formatDate(dateStr?: string): string {
  return trainingService.formatDate(dateStr);
}

// 初始化
onMounted(() => {
  fetchTasks();
  fetchStats();
});
</script>

<style scoped lang="scss">
.training-view {
  padding: 20px;
}

.stat-card {
  .stat-content {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .stat-icon {
    width: 64px;
    height: 64px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;

    &.pending {
      background-color: var(--el-color-warning-light-9);
      color: var(--el-color-warning);
    }

    &.completed {
      background-color: var(--el-color-success-light-9);
      color: var(--el-color-success);
    }

    &.total {
      background-color: var(--el-color-primary-light-9);
      color: var(--el-color-primary);
    }

    &.rate {
      background-color: var(--el-color-info-light-9);
      color: var(--el-color-info);
    }
  }

  .stat-info {
    flex: 1;
  }

  .stat-value {
    font-size: 28px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    line-height: 1.2;
  }

  .stat-label {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
  }
}

.task-list-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .filter-badge {
    margin-left: 4px;

    :deep(.el-badge__content) {
      position: relative;
      top: -1px;
    }
  }
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

.recent-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .doc-title {
    font-weight: 500;
  }
}

.acknowledge-content {
  .task-info {
    margin: 16px 0;
    padding: 16px;
    background-color: var(--el-fill-color-light);
    border-radius: 4px;

    p {
      margin: 8px 0;
      line-height: 1.6;
    }
  }
}

:deep(.el-timeline-item__node) {
  background-color: var(--el-color-success);
}
</style>
