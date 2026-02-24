<template>
  <div class="version-compare">
    <el-page-header @back="goBack" content="版本对比" />
    
    <el-card v-loading="loading" class="compare-card">
      <template #header>
        <div class="compare-header">
          <div class="version-selector">
            <el-select
              v-model="v1Id"
              placeholder="选择旧版本"
              style="width: 200px"
              @change="onVersionChange"
            >
              <el-option
                v-for="v in allVersions"
                :key="v.id"
                :label="v.version_label || `V${v.version_number}`"
                :value="v.id"
                :disabled="v.id === v2Id"
              />
            </el-select>
            <span class="compare-arrow">→</span>
            <el-select
              v-model="v2Id"
              placeholder="选择新版本"
              style="width: 200px"
              @change="onVersionChange"
            >
              <el-option
                v-for="v in allVersions"
                :key="v.id"
                :label="v.version_label || `V${v.version_number}`"
                :value="v.id"
                :disabled="v.id === v1Id"
              />
            </el-select>
          </div>
          <el-button type="primary" @click="fetchComparison" :disabled="!v1Id || !v2Id">
            开始对比
          </el-button>
        </div>
      </template>

      <template v-if="comparisonResult">
        <!-- 对比统计 -->
        <div class="statistics-bar">
          <el-statistic title="新增" :value="comparisonResult.statistics.added_count">
            <template #suffix>
              <el-tag type="success" size="small">新增</el-tag>
            </template>
          </el-statistic>
          <el-statistic title="删除" :value="comparisonResult.statistics.removed_count">
            <template #suffix>
              <el-tag type="danger" size="small">删除</el-tag>
            </template>
          </el-statistic>
          <el-statistic title="修改" :value="comparisonResult.statistics.modified_count">
            <template #suffix>
              <el-tag type="warning" size="small">修改</el-tag>
            </template>
          </el-statistic>
        </div>

        <!-- 变更摘要 -->
        <div v-if="comparisonResult.change_summary" class="change-summary">
          <el-alert
            :title="`变更摘要：${comparisonResult.change_summary}`"
            type="info"
            :closable="false"
          />
        </div>

        <!-- 版本信息对比 -->
        <div class="version-info-compare">
          <div class="version-info-box old-version">
            <h4>{{ comparisonResult.v1_version_label }}</h4>
            <el-tag size="small">旧版本</el-tag>
          </div>
          <div class="version-info-box new-version">
            <h4>{{ comparisonResult.v2_version_label }}</h4>
            <el-tag type="success" size="small">新版本</el-tag>
          </div>
        </div>

        <!-- 差异详情 -->
        <div class="diff-content">
          <!-- 新增内容 -->
          <div v-if="comparisonResult.added.length > 0" class="diff-section">
            <div class="section-header">
              <el-tag type="success">新增内容</el-tag>
              <span class="count">{{ comparisonResult.added.length }} 处</span>
            </div>
            <div class="diff-list">
              <div
                v-for="(item, index) in comparisonResult.added"
                :key="`added-${index}`"
                class="diff-item added"
              >
                <div class="diff-line-number">+</div>
                <div class="diff-text">{{ item.text }}</div>
                <div v-if="item.context" class="diff-context">{{ item.context }}</div>
              </div>
            </div>
          </div>

          <!-- 删除内容 -->
          <div v-if="comparisonResult.removed.length > 0" class="diff-section">
            <div class="section-header">
              <el-tag type="danger">删除内容</el-tag>
              <span class="count">{{ comparisonResult.removed.length }} 处</span>
            </div>
            <div class="diff-list">
              <div
                v-for="(item, index) in comparisonResult.removed"
                :key="`removed-${index}`"
                class="diff-item removed"
              >
                <div class="diff-line-number">-</div>
                <div class="diff-text">{{ item.text }}</div>
                <div v-if="item.context" class="diff-context">{{ item.context }}</div>
              </div>
            </div>
          </div>

          <!-- 修改内容 -->
          <div v-if="comparisonResult.modified.length > 0" class="diff-section">
            <div class="section-header">
              <el-tag type="warning">修改内容</el-tag>
              <span class="count">{{ comparisonResult.modified.length }} 处</span>
            </div>
            <div class="diff-list">
              <div
                v-for="(item, index) in comparisonResult.modified"
                :key="`modified-${index}`"
                class="diff-item modified"
              >
                <div class="diff-line-number">~</div>
                <div class="diff-text">{{ item.text }}</div>
                <div v-if="item.context" class="diff-context">{{ item.context }}</div>
              </div>
            </div>
          </div>

          <!-- 无差异提示 -->
          <el-empty
            v-if="comparisonResult.added.length === 0 && 
                  comparisonResult.removed.length === 0 && 
                  comparisonResult.modified.length === 0"
            description="两个版本内容相同，无差异"
          />
        </div>
      </template>

      <!-- 空状态 -->
      <el-empty
        v-else-if="!loading"
        description="请选择两个版本进行对比"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import documentVersionService, { VersionComparison, Version } from '@/services/documentVersion';

const route = useRoute();
const router = useRouter();

// URL 参数
const queryV1 = computed(() => route.query.v1 as string);
const queryV2 = computed(() => route.query.v2 as string);
const documentId = computed(() => route.query.documentId as string);

// 数据
const loading = ref(false);
const v1Id = ref('');
const v2Id = ref('');
const allVersions = ref<Version[]>([]);
const comparisonResult = ref<VersionComparison | null>(null);

// 获取文档所有版本
const fetchVersions = async () => {
  if (!documentId.value) {
    // 如果没有 documentId，尝试从版本ID推断
    if (v1Id.value) {
      try {
        const v1Detail = await documentVersionService.getVersionDetail(v1Id.value);
        if (v1Detail?.version?.document_id) {
          const docVersions = await documentVersionService.getDocumentVersions(
            v1Detail.version.document_id,
            { pageSize: 100 }
          );
          allVersions.value = docVersions.items;
        }
      } catch (error) {
        console.error('获取版本列表失败:', error);
      }
    }
    return;
  }

  try {
    const response = await documentVersionService.getDocumentVersions(documentId.value, {
      pageSize: 100,
      sortBy: 'version_number',
      sortOrder: 'asc',
    });
    allVersions.value = response.items;
  } catch (error) {
    ElMessage.error('获取版本列表失败：' + (error as Error).message);
  }
};

// 获取版本对比
const fetchComparison = async () => {
  if (!v1Id.value || !v2Id.value) {
    ElMessage.warning('请选择两个版本进行对比');
    return;
  }

  loading.value = true;
  try {
    comparisonResult.value = await documentVersionService.compareVersions(v1Id.value, v2Id.value);
  } catch (error) {
    ElMessage.error('版本对比失败：' + (error as Error).message);
  } finally {
    loading.value = false;
  }
};

// 版本选择变化
const onVersionChange = () => {
  // 如果两个版本都选择了，自动开始对比
  if (v1Id.value && v2Id.value) {
    fetchComparison();
  }
};

// 返回上一页
const goBack = () => {
  router.back();
};

// 初始化
onMounted(async () => {
  // 从 URL 参数初始化版本选择
  if (queryV1.value) {
    v1Id.value = queryV1.value;
  }
  if (queryV2.value) {
    v2Id.value = queryV2.value;
  }

  // 获取版本列表
  await fetchVersions();

  // 如果两个版本都已选择，自动对比
  if (v1Id.value && v2Id.value) {
    fetchComparison();
  }
});

// 监听 URL 参数变化
watch([queryV1, queryV2], ([newV1, newV2]) => {
  if (newV1) v1Id.value = newV1;
  if (newV2) v2Id.value = newV2;
  if (newV1 && newV2) {
    fetchComparison();
  }
});
</script>

<style scoped lang="scss">
.version-compare {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.compare-card {
  margin-top: 20px;
}

.compare-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.version-selector {
  display: flex;
  align-items: center;
  gap: 15px;
}

.compare-arrow {
  font-size: 20px;
  color: var(--el-text-color-secondary);
}

.statistics-bar {
  display: flex;
  justify-content: center;
  gap: 60px;
  padding: 20px 0;
  margin-bottom: 20px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
}

.change-summary {
  margin-bottom: 20px;
}

.version-info-compare {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 15px;
  background-color: var(--el-fill-color-light);
  border-radius: 8px;
}

.version-info-box {
  display: flex;
  align-items: center;
  gap: 10px;

  h4 {
    margin: 0;
    font-size: 16px;
  }

  &.old-version {
    h4 {
      color: var(--el-text-color-regular);
    }
  }

  &.new-version {
    h4 {
      color: var(--el-color-success);
    }
  }
}

.diff-content {
  .diff-section {
    margin-bottom: 30px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--el-border-color-light);

    .count {
      color: var(--el-text-color-secondary);
      font-size: 14px;
    }
  }

  .diff-list {
    border: 1px solid var(--el-border-color-light);
    border-radius: 4px;
    overflow: hidden;
  }

  .diff-item {
    display: flex;
    padding: 10px 15px;
    border-bottom: 1px solid var(--el-border-color-light);
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 14px;
    line-height: 1.6;

    &:last-child {
      border-bottom: none;
    }

    &.added {
      background-color: var(--el-color-success-light-9);

      .diff-line-number {
        color: var(--el-color-success);
      }
    }

    &.removed {
      background-color: var(--el-color-danger-light-9);

      .diff-line-number {
        color: var(--el-color-danger);
      }
    }

    &.modified {
      background-color: var(--el-color-warning-light-9);

      .diff-line-number {
        color: var(--el-color-warning);
      }
    }

    .diff-line-number {
      width: 30px;
      flex-shrink: 0;
      font-weight: bold;
      user-select: none;
    }

    .diff-text {
      flex: 1;
      white-space: pre-wrap;
      word-break: break-all;
    }

    .diff-context {
      width: 100%;
      margin-top: 5px;
      padding-left: 30px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
      font-style: italic;
    }
  }
}

:deep(.el-statistic__content) {
  font-size: 24px;
  font-weight: bold;
}

:deep(.el-statistic__title) {
  font-size: 14px;
  margin-bottom: 8px;
}
</style>
