/**
 * 上传管理 Store
 * 管理文件上传、去重检测、上传队列等功能
 */

import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  calculateFileHash,
  calculateFileHashFast,
  isCryptoSupported,
  type DuplicateCheckResult,
  type DuplicateType,
} from '@/utils/fileHash';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

/**
 * 上传文件项
 */
export interface UploadFileItem {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  hash: string;
  status: 'pending' | 'checking' | 'duplicated' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  duplicateResult?: DuplicateCheckResult;
  metadata?: UploadMetadata;
}

/**
 * 上传元数据
 */
export interface UploadMetadata {
  title: string;
  docCode?: string;
  docType?: string;
  changeSummary: string;
  changeDetails?: string;
  effectiveDate?: string;
  kbId: string;
}

/**
 * 去重检测请求参数
 */
interface DuplicateCheckRequest {
  fileHash: string;
  filename: string;
  kbId: string;
}

/**
 * 上传服务类
 */
class UploadService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/upload`;
  }

  /**
   * 检查文件是否重复
   */
  async checkDuplicate(params: DuplicateCheckRequest): Promise<DuplicateCheckResult> {
    const url = `${this.baseUrl}/check-duplicate`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '去重检测失败');
    }

    return result.data;
  }

  /**
   * 上传新文档
   */
  async uploadDocument(file: File, metadata: UploadMetadata, onProgress?: (progress: number) => void): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', metadata.title);
    formData.append('kb_id', metadata.kbId);
    if (metadata.docCode) formData.append('doc_code', metadata.docCode);
    if (metadata.docType) formData.append('doc_type', metadata.docType);
    formData.append('change_summary', metadata.changeSummary);
    if (metadata.changeDetails) formData.append('change_details', metadata.changeDetails);
    if (metadata.effectiveDate) formData.append('effective_date', metadata.effectiveDate);

    return this.uploadWithProgress(`${API_BASE_URL}/documents`, formData, onProgress);
  }

  /**
   * 上传新版本
   */
  async uploadNewVersion(
    documentId: string,
    file: File,
    metadata: Partial<UploadMetadata>,
    onProgress?: (progress: number) => void
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('change_summary', metadata.changeSummary || '');
    if (metadata.changeDetails) formData.append('change_details', metadata.changeDetails);
    if (metadata.effectiveDate) formData.append('effective_date', metadata.effectiveDate);

    return this.uploadWithProgress(
      `${API_BASE_URL}/documents/${documentId}/versions`,
      formData,
      onProgress
    );
  }

  /**
   * 带进度监控的上传
   */
  private uploadWithProgress(url: string, formData: FormData, onProgress?: (progress: number) => void): Promise<any> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const result = JSON.parse(xhr.responseText);
          resolve(result);
        } else {
          reject(new Error(`上传失败: ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('上传过程中发生错误'));
      });

      xhr.open('POST', url);
      xhr.send(formData);
    });
  }
}

// 创建上传服务实例
const uploadService = new UploadService();

/**
 * 上传 Store
 */
export const useUploadStore = defineStore('upload', () => {
  // 路由实例（在 setup 中初始化）
  let router: ReturnType<typeof useRouter> | null = null;

  // 状态
  const uploadQueue = ref<UploadFileItem[]>([]);
  const currentKbId = ref<string>('default');
  const isProcessing = ref(false);
  const duplicateDialogVisible = ref(false);
  const currentDuplicateFile = ref<UploadFileItem | null>(null);
  const renameDialogVisible = ref(false);
  const newVersionDialogVisible = ref(false);
  const currentNewVersionDoc = ref<any>(null);

  // 计算属性
  const pendingFiles = computed(() => uploadQueue.value.filter(f => f.status === 'pending'));
  const uploadingFiles = computed(() => uploadQueue.value.filter(f => f.status === 'uploading'));
  const completedFiles = computed(() => uploadQueue.value.filter(f => f.status === 'success'));
  const hasErrors = computed(() => uploadQueue.value.some(f => f.status === 'error'));
  const totalProgress = computed(() => {
    if (uploadQueue.value.length === 0) return 0;
    const total = uploadQueue.value.reduce((sum, f) => sum + f.progress, 0);
    return Math.round(total / uploadQueue.value.length);
  });

  /**
   * 初始化路由
   */
  function initRouter() {
    if (!router) {
      router = useRouter();
    }
  }

  /**
   * 生成唯一ID
   */
  function generateId(): string {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 检查文件是否重复
   */
  async function checkDuplicate(file: File): Promise<DuplicateCheckResult> {
    // 检查浏览器是否支持 Crypto API
    if (!isCryptoSupported()) {
      // 不支持则跳过哈希计算，直接返回新文件
      return {
        type: 'new_file',
        message: '浏览器不支持哈希计算，跳过去重检测',
        suggestions: ['正常上传'],
      };
    }

    // 计算文件哈希
    const hash = await calculateFileHashFast(file);

    // 调用 API 检查重复
    const result = await uploadService.checkDuplicate({
      fileHash: hash,
      filename: file.name,
      kbId: currentKbId.value,
    });

    return result;
  }

  /**
   * 添加文件到队列（带去重检测）
   */
  async function addFileWithCheck(file: File, metadata?: Partial<UploadMetadata>): Promise<void> {
    initRouter();

    // 创建上传项
    const uploadItem: UploadFileItem = {
      id: generateId(),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      hash: '',
      status: 'checking',
      progress: 0,
      metadata: metadata as UploadMetadata,
    };

    uploadQueue.value.push(uploadItem);

    try {
      // 计算哈希
      if (isCryptoSupported()) {
        uploadItem.hash = await calculateFileHashFast(file);
      }

      // 检查重复
      const checkResult = await checkDuplicate(file);
      uploadItem.duplicateResult = checkResult;

      if (checkResult.type === 'exact_match') {
        // 完全相同的文件
        uploadItem.status = 'duplicated';
        showDuplicateDialog(uploadItem, checkResult);
      } else if (checkResult.type === 'name_match') {
        // 同名不同内容
        uploadItem.status = 'duplicated';
        showNameMatchDialog(uploadItem, checkResult);
      } else {
        // 新文件，直接添加到待上传队列
        uploadItem.status = 'pending';
      }
    } catch (error) {
      uploadItem.status = 'error';
      uploadItem.error = (error as Error).message;
      ElMessage.error(`文件检查失败: ${uploadItem.error}`);
    }
  }

  /**
   * 显示完全重复对话框
   */
  function showDuplicateDialog(fileItem: UploadFileItem, result: DuplicateCheckResult) {
    currentDuplicateFile.value = fileItem;

    const doc = result.existingDocument;
    const versionLabel = doc?.currentVersion?.versionLabel || `V${doc?.currentVersion?.versionNumber}`;
    const statusText = getStatusText(doc?.currentVersion?.status || '');

    ElMessageBox.confirm(
      `
      <div style="text-align: left;">
        <p><strong>该文件已存在</strong></p>
        <p>文档: ${doc?.title || doc?.filename || '未知文档'}</p>
        <p>当前版本: ${versionLabel} (${statusText})</p>
      </div>
      `,
      '文件已存在',
      {
        confirmButtonText: '作为新版本上传',
        cancelButtonText: '查看现有版本',
        distinguishCancelAndClose: true,
        dangerouslyUseHTMLString: true,
        showClose: true,
      }
    )
      .then(() => {
        // 作为新版本上传
        handleDuplicateAction('upload_as_new_version', fileItem, result);
      })
      .catch((action) => {
        if (action === 'cancel') {
          // 查看现有版本
          handleDuplicateAction('view', fileItem, result);
        } else {
          // 关闭对话框（取消）
          handleDuplicateAction('cancel', fileItem, result);
        }
      });
  }

  /**
   * 显示同名匹配对话框
   */
  function showNameMatchDialog(fileItem: UploadFileItem, result: DuplicateCheckResult) {
    currentDuplicateFile.value = fileItem;

    const doc = result.existingDocument;
    const currentVersion = doc?.currentVersion;
    const nextVersionNumber = (currentVersion?.versionNumber || 0) + 1;
    const nextVersionLabel = `V${Math.floor(nextVersionNumber / 10)}.${nextVersionNumber % 10}`;

    ElMessageBox.confirm(
      `
      <div style="text-align: left;">
        <p><strong>检测到同名文档</strong></p>
        <p>现有版本: ${doc?.title || doc?.filename || '未知文档'} ${currentVersion?.versionLabel || `V${currentVersion?.versionNumber}`}</p>
        <p>是否创建为新版本 <strong>${nextVersionLabel}</strong>？</p>
      </div>
      `,
      '创建新版本',
      {
        confirmButtonText: `创建新版本 ${nextVersionLabel}`,
        cancelButtonText: '重命名上传',
        distinguishCancelAndClose: true,
        dangerouslyUseHTMLString: true,
        showClose: true,
      }
    )
      .then(() => {
        // 创建为新版本
        handleDuplicateAction('upload_as_new_version', fileItem, result);
      })
      .catch((action) => {
        if (action === 'cancel') {
          // 重命名上传
          handleDuplicateAction('rename', fileItem, result);
        } else {
          // 关闭对话框（取消）
          handleDuplicateAction('cancel', fileItem, result);
        }
      });
  }

  /**
   * 处理去重操作
   */
  async function handleDuplicateAction(
    action: string,
    fileItem: UploadFileItem,
    checkResult: DuplicateCheckResult
  ): Promise<void> {
    switch (action) {
      case 'view':
        // 查看现有版本
        if (checkResult.existingDocument?.id && router) {
          router.push(`/documents/${checkResult.existingDocument.id}/versions`);
        }
        // 从队列中移除
        removeFromQueue(fileItem.id);
        break;

      case 'upload_as_new_version':
        // 作为新版本上传
        if (checkResult.existingDocument) {
          currentNewVersionDoc.value = checkResult.existingDocument;
          newVersionDialogVisible.value = true;
          // 更新文件项状态
          const item = uploadQueue.value.find(f => f.id === fileItem.id);
          if (item) {
            item.status = 'pending';
          }
        }
        break;

      case 'rename':
        // 打开重命名对话框
        renameDialogVisible.value = true;
        break;

      case 'cancel':
        // 取消上传，从队列中移除
        removeFromQueue(fileItem.id);
        break;
    }
  }

  /**
   * 从队列中移除文件
   */
  function removeFromQueue(fileId: string): void {
    const index = uploadQueue.value.findIndex(f => f.id === fileId);
    if (index > -1) {
      uploadQueue.value.splice(index, 1);
    }
  }

  /**
   * 开始上传单个文件
   */
  async function uploadFile(fileId: string): Promise<void> {
    const fileItem = uploadQueue.value.find(f => f.id === fileId);
    if (!fileItem || !fileItem.metadata) return;

    fileItem.status = 'uploading';

    try {
      const onProgress = (progress: number) => {
        fileItem.progress = progress;
      };

      await uploadService.uploadDocument(fileItem.file, fileItem.metadata, onProgress);

      fileItem.status = 'success';
      fileItem.progress = 100;
      ElMessage.success(`「${fileItem.name}」上传成功`);
    } catch (error) {
      fileItem.status = 'error';
      fileItem.error = (error as Error).message;
      ElMessage.error(`「${fileItem.name}」上传失败: ${fileItem.error}`);
    }
  }

  /**
   * 上传新版本
   */
  async function uploadAsNewVersion(
    documentId: string,
    fileId: string,
    metadata: Partial<UploadMetadata>
  ): Promise<void> {
    const fileItem = uploadQueue.value.find(f => f.id === fileId);
    if (!fileItem) return;

    fileItem.status = 'uploading';

    try {
      const onProgress = (progress: number) => {
        fileItem.progress = progress;
      };

      await uploadService.uploadNewVersion(documentId, fileItem.file, metadata, onProgress);

      fileItem.status = 'success';
      fileItem.progress = 100;
      ElMessage.success(`「${fileItem.name}」新版本上传成功`);

      // 关闭对话框
      newVersionDialogVisible.value = false;
    } catch (error) {
      fileItem.status = 'error';
      fileItem.error = (error as Error).message;
      ElMessage.error(`「${fileItem.name}」上传失败: ${fileItem.error}`);
    }
  }

  /**
   * 开始处理上传队列
   */
  async function processQueue(): Promise<void> {
    if (isProcessing.value) return;

    isProcessing.value = true;

    try {
      const pending = pendingFiles.value;
      for (const file of pending) {
        await uploadFile(file.id);
      }
    } finally {
      isProcessing.value = false;
    }
  }

  /**
   * 清空已完成和失败的文件
   */
  function clearCompleted(): void {
    uploadQueue.value = uploadQueue.value.filter(
      f => f.status !== 'success' && f.status !== 'error'
    );
  }

  /**
   * 清空所有文件
   */
  function clearAll(): void {
    uploadQueue.value = [];
  }

  /**
   * 重试上传失败的文件
   */
  async function retryFile(fileId: string): Promise<void> {
    const fileItem = uploadQueue.value.find(f => f.id === fileId);
    if (!fileItem) return;

    fileItem.status = 'pending';
    fileItem.progress = 0;
    fileItem.error = undefined;

    await uploadFile(fileId);
  }

  /**
   * 设置当前知识库
   */
  function setCurrentKbId(kbId: string): void {
    currentKbId.value = kbId;
  }

  /**
   * 获取状态文本
   */
  function getStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      draft: '草稿',
      review: '审核中',
      approved: '已批准',
      effective: '生效中',
      obsolete: '已作废',
      archived: '已归档',
    };
    return statusMap[status] || status;
  }

  return {
    // 状态
    uploadQueue,
    currentKbId,
    isProcessing,
    duplicateDialogVisible,
    currentDuplicateFile,
    renameDialogVisible,
    newVersionDialogVisible,
    currentNewVersionDoc,

    // 计算属性
    pendingFiles,
    uploadingFiles,
    completedFiles,
    hasErrors,
    totalProgress,

    // 方法
    initRouter,
    checkDuplicate,
    addFileWithCheck,
    handleDuplicateAction,
    removeFromQueue,
    uploadFile,
    uploadAsNewVersion,
    processQueue,
    clearCompleted,
    clearAll,
    retryFile,
    setCurrentKbId,
    getStatusText,
  };
});

export default useUploadStore;
