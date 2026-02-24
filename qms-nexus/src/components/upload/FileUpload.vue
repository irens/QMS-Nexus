<template>
  <div class="file-upload">
    <!-- 拖拽上传区域 -->
    <div
      class="upload-dropzone"
      :class="{ 'is-dragover': isDragOver, 'is-disabled': isProcessing }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        multiple
        accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt"
        style="display: none"
        @change="handleFileSelect"
      />
      <div class="upload-content">
        <el-icon class="upload-icon" :size="48"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p class="main-text">点击或拖拽文件到此处上传</p>
          <p class="sub-text">支持 PDF、Word、Excel、PPT、TXT 等格式</p>
        </div>
        <el-button type="primary" :disabled="isProcessing">
          <el-icon><Plus /></el-icon>
          选择文件
        </el-button>
      </div>
    </div>

    <!-- 上传队列列表 -->
    <div v-if="uploadQueue.length > 0" class="upload-queue">
      <div class="queue-header">
        <span class="queue-title">上传队列 ({{ uploadQueue.length }})</span>
        <div class="queue-actions">
          <el-button
            v-if="hasCompletedFiles"
            size="small"
            @click="clearCompleted"
          >
            清空已完成
          </el-button>
          <el-button
            v-if="uploadQueue.length > 0"
            size="small"
            type="danger"
            @click="clearAll"
          >
            清空全部
          </el-button>
        </div>
      </div>

      <div class="queue-list">
        <div
          v-for="item in uploadQueue"
          :key="item.id"
          class="queue-item"
          :class="`status-${item.status}`"
        >
          <!-- 文件图标 -->
          <div class="file-icon">
            <el-icon :size="24">
              <Document v-if="isDocument(item.type)" />
              <Picture v-else-if="isImage(item.type)" />
              <Files v-else />
            </el-icon>
          </div>

          <!-- 文件信息 -->
          <div class="file-info">
            <div class="file-name" :title="item.name">{{ item.name }}</div>
            <div class="file-meta">
              <span class="file-size">{{ formatFileSize(item.size) }}</span>
              <span v-if="item.hash" class="file-hash" :title="item.hash">
                指纹: {{ getFileFingerprint(item.hash) }}
              </span>
            </div>
          </div>

          <!-- 状态显示 -->
          <div class="file-status">
            <el-tag
              v-if="item.status === 'checking'"
              size="small"
              type="info"
            >
              <el-icon class="is-loading"><Loading /></el-icon>
              检测中
            </el-tag>
            <el-tag
              v-else-if="item.status === 'duplicated'"
              size="small"
              type="warning"
            >
              发现重复
            </el-tag>
            <el-tag
              v-else-if="item.status === 'pending'"
              size="small"
            >
              等待上传
            </el-tag>
            <el-tag
              v-else-if="item.status === 'uploading'"
              size="small"
              type="primary"
            >
              上传中 {{ item.progress }}%
            </el-tag>
            <el-tag
              v-else-if="item.status === 'success'"
              size="small"
              type="success"
            >
              <el-icon><Check /></el-icon>
              完成
            </el-tag>
            <el-tag
              v-else-if="item.status === 'error'"
              size="small"
              type="danger"
            >
              失败
            </el-tag>
          </div>

          <!-- 操作按钮 -->
          <div class="file-actions">
            <el-button
              v-if="item.status === 'error'"
              size="small"
              type="primary"
              @click="retryFile(item.id)"
            >
              重试
            </el-button>
            <el-button
              v-if="item.status !== 'uploading'"
              size="small"
              type="danger"
              text
              @click="removeFromQueue(item.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>

          <!-- 进度条 -->
          <div
            v-if="item.status === 'uploading' || item.status === 'success'"
            class="file-progress"
          >
            <el-progress
              :percentage="item.progress"
              :status="item.status === 'success' ? 'success' : undefined"
              :show-text="false"
            />
          </div>
        </div>
      </div>

      <!-- 批量操作 -->
      <div v-if="pendingFiles.length > 0" class="batch-actions">
        <el-button
          type="primary"
          :loading="isProcessing"
          @click="startUpload"
        >
          开始上传 ({{ pendingFiles.length }})
        </el-button>
      </div>
    </div>

    <!-- 去重提示对话框 -->
    <el-dialog
      v-model="duplicateDialogVisible"
      title="文件已存在"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="currentDuplicateFile?.duplicateResult" class="duplicate-content">
        <el-alert
          title="检测到完全相同的文件"
          type="warning"
          :closable="false"
          show-icon
        />
        <div class="duplicate-info">
          <p><strong>文档名称:</strong> {{ currentDuplicateFile.duplicateResult.existingDocument?.title }}</p>
          <p><strong>当前版本:</strong> {{ currentDuplicateFile.duplicateResult.existingDocument?.currentVersion?.versionLabel }}</p>
          <p><strong>状态:</strong> {{ getStatusText(currentDuplicateFile.duplicateResult.existingDocument?.currentVersion?.status || '') }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="handleDuplicateCancel">取消</el-button>
        <el-button type="primary" @click="handleDuplicateView">查看现有版本</el-button>
        <el-button type="success" @click="handleDuplicateUploadNew">作为新版本上传</el-button>
      </template>
    </el-dialog>

    <!-- 同名提示对话框 -->
    <el-dialog
      v-model="nameMatchDialogVisible"
      title="检测到同名文档"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="currentDuplicateFile?.duplicateResult" class="duplicate-content">
        <el-alert
          title="同名文档已存在"
          type="info"
          :closable="false"
          show-icon
        />
        <div class="duplicate-info">
          <p><strong>文档名称:</strong> {{ currentDuplicateFile.duplicateResult.existingDocument?.title }}</p>
          <p><strong>现有版本:</strong> {{ currentDuplicateFile.duplicateResult.existingDocument?.currentVersion?.versionLabel }}</p>
          <p><strong>建议操作:</strong> 创建为新版本或重命名上传</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="handleNameMatchCancel">取消</el-button>
        <el-button @click="handleNameMatchRename">重命名上传</el-button>
        <el-button type="primary" @click="handleNameMatchNewVersion">创建新版本</el-button>
      </template>
    </el-dialog>

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="renameDialogVisible"
      title="重命名文件"
      width="400px"
    >
      <el-form :model="renameForm" label-width="80px">
        <el-form-item label="新文件名">
          <el-input v-model="renameForm.newName" placeholder="请输入新文件名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确认</el-button>
      </template>
    </el-dialog>

    <!-- 新版本上传对话框 -->
    <el-dialog
      v-model="newVersionDialogVisible"
      title="上传新版本"
      width="600px"
    >
      <el-form
        ref="newVersionFormRef"
        :model="newVersionForm"
        :rules="newVersionRules"
        label-width="100px"
      >
        <el-alert
          v-if="currentNewVersionDoc"
          :title="`正在为「${currentNewVersionDoc.title || currentNewVersionDoc.filename}」创建新版本`"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />

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
        <el-button type="primary" :loading="isUploadingNewVersion" @click="confirmNewVersion">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, type FormInstance } from 'element-plus';
import {
  UploadFilled,
  Plus,
  Document,
  Picture,
  Files,
  Loading,
  Check,
  Delete,
} from '@element-plus/icons-vue';
import { useUploadStore, type UploadFileItem, type UploadMetadata } from '@/stores/upload';
import { getFileFingerprint } from '@/utils/fileHash';

const router = useRouter();
const uploadStore = useUploadStore();

// 状态
const isDragOver = ref(false);
const isProcessing = computed(() => uploadStore.isProcessing);
const uploadQueue = computed(() => uploadStore.uploadQueue);
const pendingFiles = computed(() => uploadStore.pendingFiles);
const hasCompletedFiles = computed(() => uploadStore.completedFiles.length > 0);

// Refs
const fileInputRef = ref<HTMLInputElement>();
const newVersionFormRef = ref<FormInstance>();

// 去重对话框
const duplicateDialogVisible = ref(false);
const nameMatchDialogVisible = ref(false);
const currentDuplicateFile = ref<UploadFileItem | null>(null);

// 重命名对话框
const renameDialogVisible = ref(false);
const renameForm = ref({
  newName: '',
});

// 新版本对话框
const newVersionDialogVisible = ref(false);
const isUploadingNewVersion = ref(false);
const currentNewVersionDoc = ref<any>(null);
const newVersionForm = ref({
  changeSummary: '',
  changeDetails: '',
  versionLabel: '',
  effectiveDate: '',
});

const newVersionRules = {
  changeSummary: [{ required: true, message: '请输入变更摘要', trigger: 'blur' }],
};

// 拖拽处理
function handleDragOver() {
  if (!isProcessing.value) {
    isDragOver.value = true;
  }
}

function handleDragLeave() {
  isDragOver.value = false;
}

function handleDrop(e: DragEvent) {
  isDragOver.value = false;
  if (isProcessing.value) return;

  const files = e.dataTransfer?.files;
  if (files) {
    handleFiles(Array.from(files));
  }
}

function triggerFileInput() {
  if (!isProcessing.value) {
    fileInputRef.value?.click();
  }
}

function handleFileSelect(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (files) {
    handleFiles(Array.from(files));
  }
  // 重置 input 以便可以重复选择相同文件
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
}

// 处理文件
async function handleFiles(files: File[]) {
  for (const file of files) {
    await uploadStore.addFileWithCheck(file);

    // 检查是否有重复文件需要显示对话框
    const lastItem = uploadQueue.value[uploadQueue.value.length - 1];
    if (lastItem?.status === 'duplicated' && lastItem.duplicateResult) {
      currentDuplicateFile.value = lastItem;

      if (lastItem.duplicateResult.type === 'exact_match') {
        duplicateDialogVisible.value = true;
      } else if (lastItem.duplicateResult.type === 'name_match') {
        nameMatchDialogVisible.value = true;
      }
    }
  }
}

// 开始上传
async function startUpload() {
  await uploadStore.processQueue();
}

// 重试文件
async function retryFile(fileId: string) {
  await uploadStore.retryFile(fileId);
}

// 从队列移除
function removeFromQueue(fileId: string) {
  uploadStore.removeFromQueue(fileId);
}

// 清空已完成
function clearCompleted() {
  uploadStore.clearCompleted();
}

// 清空全部
function clearAll() {
  uploadStore.clearAll();
}

// 去重对话框操作
function handleDuplicateCancel() {
  duplicateDialogVisible.value = false;
  if (currentDuplicateFile.value) {
    uploadStore.removeFromQueue(currentDuplicateFile.value.id);
  }
}

function handleDuplicateView() {
  duplicateDialogVisible.value = false;
  const docId = currentDuplicateFile.value?.duplicateResult?.existingDocument?.id;
  if (docId) {
    router.push(`/documents/${docId}/versions`);
  }
  if (currentDuplicateFile.value) {
    uploadStore.removeFromQueue(currentDuplicateFile.value.id);
  }
}

function handleDuplicateUploadNew() {
  duplicateDialogVisible.value = false;
  const doc = currentDuplicateFile.value?.duplicateResult?.existingDocument;
  if (doc) {
    currentNewVersionDoc.value = doc;
    newVersionDialogVisible.value = true;
  }
}

// 同名对话框操作
function handleNameMatchCancel() {
  nameMatchDialogVisible.value = false;
  if (currentDuplicateFile.value) {
    uploadStore.removeFromQueue(currentDuplicateFile.value.id);
  }
}

function handleNameMatchRename() {
  nameMatchDialogVisible.value = false;
  renameForm.value.newName = currentDuplicateFile.value?.name || '';
  renameDialogVisible.value = true;
}

function handleNameMatchNewVersion() {
  nameMatchDialogVisible.value = false;
  const doc = currentDuplicateFile.value?.duplicateResult?.existingDocument;
  if (doc) {
    currentNewVersionDoc.value = doc;
    newVersionDialogVisible.value = true;
  }
}

// 重命名确认
function confirmRename() {
  if (!renameForm.value.newName || !currentDuplicateFile.value) {
    ElMessage.warning('请输入新文件名');
    return;
  }

  // 创建新文件对象
  const originalFile = currentDuplicateFile.value.file;
  const renamedFile = new File([originalFile], renameForm.value.newName, {
    type: originalFile.type,
  });

  // 移除旧项，添加新项
  uploadStore.removeFromQueue(currentDuplicateFile.value.id);
  uploadStore.addFileWithCheck(renamedFile);

  renameDialogVisible.value = false;
  renameForm.value.newName = '';
}

// 新版本上传确认
async function confirmNewVersion() {
  if (!newVersionFormRef.value || !currentDuplicateFile.value || !currentNewVersionDoc.value) return;

  await newVersionFormRef.value.validate(async (valid) => {
    if (!valid) return;

    isUploadingNewVersion.value = true;
    try {
      await uploadStore.uploadAsNewVersion(
        currentNewVersionDoc.value.id,
        currentDuplicateFile.value.id,
        {
          changeSummary: newVersionForm.value.changeSummary,
          changeDetails: newVersionForm.value.changeDetails || undefined,
          versionLabel: newVersionForm.value.versionLabel || undefined,
          effectiveDate: newVersionForm.value.effectiveDate || undefined,
        }
      );

      newVersionDialogVisible.value = false;
      newVersionForm.value = {
        changeSummary: '',
        changeDetails: '',
        versionLabel: '',
        effectiveDate: '',
      };
    } catch (error) {
      ElMessage.error('上传失败: ' + (error as Error).message);
    } finally {
      isUploadingNewVersion.value = false;
    }
  });
}

// 工具函数
function isDocument(type: string): boolean {
  return type.includes('pdf') ||
    type.includes('word') ||
    type.includes('excel') ||
    type.includes('powerpoint') ||
    type.includes('text');
}

function isImage(type: string): boolean {
  return type.startsWith('image/');
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getStatusText(status: string): string {
  return uploadStore.getStatusText(status);
}
</script>

<style scoped lang="scss">
.file-upload {
  width: 100%;
}

.upload-dropzone {
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: var(--el-fill-color-light);

  &:hover {
    border-color: var(--el-color-primary);
  }

  &.is-dragover {
    border-color: var(--el-color-primary);
    background-color: var(--el-color-primary-light-9);
  }

  &.is-disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-icon {
  color: var(--el-text-color-secondary);
}

.upload-text {
  .main-text {
    font-size: 16px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;
  }

  .sub-text {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.upload-queue {
  margin-top: 24px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color);
}

.queue-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.queue-actions {
  display: flex;
  gap: 8px;
}

.queue-list {
  max-height: 400px;
  overflow-y: auto;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-light);
  transition: background-color 0.2s;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background-color: var(--el-fill-color-light);
  }

  &.status-success {
    background-color: var(--el-color-success-light-9);
  }

  &.status-error {
    background-color: var(--el-color-danger-light-9);
  }
}

.file-icon {
  flex-shrink: 0;
  color: var(--el-color-primary);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  display: flex;
  gap: 12px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.file-hash {
  font-family: monospace;
}

.file-status {
  flex-shrink: 0;
}

.file-actions {
  display: flex;
  gap: 8px;
}

.file-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
}

.batch-actions {
  display: flex;
  justify-content: center;
  padding: 16px;
  background-color: var(--el-fill-color-light);
  border-top: 1px solid var(--el-border-color);
}

.duplicate-content {
  padding: 16px 0;
}

.duplicate-info {
  margin-top: 16px;
  padding: 16px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;

  p {
    margin: 8px 0;
    line-height: 1.6;
  }
}

:deep(.el-progress__text) {
  display: none;
}
</style>
