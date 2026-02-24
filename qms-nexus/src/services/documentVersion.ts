/**
 * 文档版本管理服务
 * 提供文档版本的完整生命周期管理 API 调用
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// 类型定义
export interface Version {
  id: string;
  document_id: string;
  version_number: number;
  version_label: string;
  filename: string;
  file_hash: string;
  file_size: number;
  file_type: string;
  status: VersionStatus;
  title?: string;
  description?: string;
  change_summary?: string;
  change_details?: string;
  previous_version_id?: string;
  effective_date?: string;
  review_date?: string;
  is_latest: boolean;
  prepared_by?: string;
  reviewed_by?: string;
  approved_by?: string;
  approved_date?: string;
  kb_id: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export type VersionStatus = 'draft' | 'review' | 'approved' | 'effective' | 'obsolete' | 'archived';

export interface VersionListResponse {
  items: Version[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface VersionDetail {
  version: Version;
  approval_history: ApprovalHistory[];
  previous_version?: Version;
}

export interface ApprovalHistory {
  id: number;
  action: string;
  action_by: string;
  action_at: string;
  comment?: string;
  from_status?: string;
  to_status: string;
}

export interface VersionComparison {
  v1_id: string;
  v2_id: string;
  v1_version_label: string;
  v2_version_label: string;
  added: DiffChunk[];
  removed: DiffChunk[];
  modified: DiffChunk[];
  statistics: {
    added_count: number;
    removed_count: number;
    modified_count: number;
  };
  change_summary?: string;
}

export interface DiffChunk {
  text: string;
  line_number?: number;
  context?: string;
}

export interface UploadResponse {
  version_id: string;
  version_number: number;
  version_label?: string;
  status: VersionStatus;
  file_hash: string;
}

export interface UploadVersionData {
  changeSummary: string;
  changeDetails?: string;
  versionLabel?: string;
  effectiveDate?: Date;
}

export interface VersionListParams {
  status?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// API 响应格式
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

/**
 * 文档版本管理服务类
 */
export class DocumentVersionService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/documents`;
  }

  /**
   * 获取文档版本历史列表
   */
  async getDocumentVersions(
    documentId: string,
    params?: VersionListParams
  ): Promise<VersionListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());
    if (params?.sortBy) queryParams.append('sort_by', params.sortBy);
    if (params?.sortOrder) queryParams.append('sort_order', params.sortOrder);

    const url = `${this.baseUrl}/${documentId}/versions?${queryParams.toString()}`;
    const response = await fetch(url);
    const result: ApiResponse<VersionListResponse> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取版本列表失败');
    }

    return result.data;
  }

  /**
   * 获取版本详情
   */
  async getVersionDetail(versionId: string): Promise<VersionDetail> {
    const url = `${this.baseUrl}/versions/${versionId}`;
    const response = await fetch(url);
    const result: ApiResponse<VersionDetail> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取版本详情失败');
    }

    return result.data;
  }

  /**
   * 上传新版本
   */
  async uploadNewVersion(
    documentId: string,
    file: File,
    data: UploadVersionData
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('change_summary', data.changeSummary);
    if (data.changeDetails) formData.append('change_details', data.changeDetails);
    if (data.versionLabel) formData.append('version_label', data.versionLabel);
    if (data.effectiveDate) formData.append('effective_date', data.effectiveDate.toISOString());

    const url = `${this.baseUrl}/${documentId}/versions`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    const result: ApiResponse<UploadResponse> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '上传新版本失败');
    }

    return result.data;
  }

  /**
   * 提交版本审核
   */
  async submitForReview(versionId: string, comment?: string): Promise<void> {
    const formData = new FormData();
    if (comment) formData.append('comment', comment);

    const url = `${this.baseUrl}/versions/${versionId}/submit`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '提交审核失败');
    }
  }

  /**
   * 审批通过版本
   */
  async approveVersion(versionId: string, comment?: string): Promise<void> {
    const url = `${this.baseUrl}/versions/${versionId}/approve`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment }),
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '审批失败');
    }
  }

  /**
   * 审批拒绝版本
   */
  async rejectVersion(versionId: string, comment: string): Promise<void> {
    const url = `${this.baseUrl}/versions/${versionId}/reject`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment }),
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '拒绝失败');
    }
  }

  /**
   * 作废版本
   */
  async obsoleteVersion(versionId: string, reason?: string): Promise<void> {
    const url = `${this.baseUrl}/versions/${versionId}/obsolete`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '作废失败');
    }
  }

  /**
   * 对比两个版本
   */
  async compareVersions(v1Id: string, v2Id: string): Promise<VersionComparison> {
    const url = `${this.baseUrl}/versions/${v1Id}/compare/${v2Id}`;
    const response = await fetch(url);
    const result: ApiResponse<VersionComparison> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '版本对比失败');
    }

    return result.data;
  }

  /**
   * 下载版本文件
   */
  async downloadVersion(versionId: string): Promise<Blob> {
    const url = `${this.baseUrl}/versions/${versionId}/download`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error('下载失败');
    }

    return await response.blob();
  }

  /**
   * 获取版本状态文本
   */
  static getStatusText(status: VersionStatus): string {
    const statusMap: Record<VersionStatus, string> = {
      draft: '草稿',
      review: '审核中',
      approved: '已批准',
      effective: '生效中',
      obsolete: '已作废',
      archived: '已归档',
    };
    return statusMap[status] || status;
  }

  /**
   * 获取版本状态标签类型
   */
  static getStatusType(status: VersionStatus): '' | 'success' | 'warning' | 'danger' | 'info' {
    const typeMap: Record<VersionStatus, '' | 'success' | 'warning' | 'danger' | 'info'> = {
      draft: 'info',
      review: 'warning',
      approved: '',
      effective: 'success',
      obsolete: 'danger',
      archived: 'info',
    };
    return typeMap[status] || '';
  }

  /**
   * 获取时间轴项目类型
   */
  static getTimelineItemType(status: VersionStatus): '' | 'primary' | 'success' | 'warning' | 'danger' | 'info' {
    const typeMap: Record<VersionStatus, '' | 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
      draft: 'info',
      review: 'warning',
      approved: 'primary',
      effective: 'success',
      obsolete: 'danger',
      archived: 'info',
    };
    return typeMap[status] || '';
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 格式化日期
   */
  static formatDate(dateStr?: string): string {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  }

  /**
   * 格式化日期时间
   */
  static formatDateTime(dateStr?: string): string {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}

// 导出单例实例
export const documentVersionService = new DocumentVersionService();
export default documentVersionService;
