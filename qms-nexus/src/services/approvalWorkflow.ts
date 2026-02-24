/**
 * 审批工作流服务
 * 提供文档审批相关的 API 调用
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// 类型定义
export interface PendingReviewItem {
  id: string;
  version_id: string;
  document_id: string;
  document_title: string;
  document_code?: string;
  filename: string;
  version_number: number;
  version_label: string;
  change_summary: string;
  change_details?: string;
  submitted_by: string;
  submitted_at: string;
  previous_version_id?: string;
  previous_version_label?: string;
}

export interface ReviewHistoryItem {
  id: string;
  version_id: string;
  document_id: string;
  document_title: string;
  version_label: string;
  action: 'approve' | 'reject';
  action_by: string;
  action_at: string;
  comment?: string;
}

export interface MySubmissionItem {
  id: string;
  version_id: string;
  document_id: string;
  document_title: string;
  version_label: string;
  status: 'draft' | 'review' | 'approved' | 'effective' | 'obsolete';
  submitted_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
  comment?: string;
}

export interface ReviewDetail {
  version: {
    id: string;
    document_id: string;
    version_number: number;
    version_label: string;
    filename: string;
    file_size: number;
    file_type: string;
    status: string;
    title?: string;
    change_summary: string;
    change_details?: string;
    previous_version_id?: string;
    submitted_by: string;
    submitted_at: string;
  };
  document: {
    id: string;
    title: string;
    doc_code?: string;
    doc_type?: string;
  };
  previous_version?: {
    id: string;
    version_label: string;
    change_summary: string;
  };
  approval_history: Array<{
    id: number;
    action: string;
    action_by: string;
    action_at: string;
    comment?: string;
  }>;
}

export interface ApproveRequest {
  comment?: string;
}

export interface RejectRequest {
  comment: string;
}

export interface ReviewListParams {
  page?: number;
  pageSize?: number;
}

// API 响应格式
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

/**
 * 审批工作流服务类
 */
export class ApprovalWorkflowService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/documents`;
  }

  /**
   * 获取待审批列表
   */
  async getPendingReviews(params?: ReviewListParams): Promise<{
    items: PendingReviewItem[];
    total: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());

    const url = `${this.baseUrl}/pending-review?${queryParams.toString()}`;
    const response = await fetch(url);
    const result: ApiResponse<{ items: PendingReviewItem[]; total: number }> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取待审批列表失败');
    }

    return result.data;
  }

  /**
   * 获取审批详情
   */
  async getReviewDetail(versionId: string): Promise<ReviewDetail> {
    const url = `${this.baseUrl}/versions/${versionId}/review-detail`;
    const response = await fetch(url);
    const result: ApiResponse<ReviewDetail> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取审批详情失败');
    }

    return result.data;
  }

  /**
   * 审批通过
   */
  async approveVersion(versionId: string, data: ApproveRequest): Promise<void> {
    const url = `${this.baseUrl}/versions/${versionId}/approve`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '审批失败');
    }
  }

  /**
   * 审批拒绝
   */
  async rejectVersion(versionId: string, data: RejectRequest): Promise<void> {
    const url = `${this.baseUrl}/versions/${versionId}/reject`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '拒绝失败');
    }
  }

  /**
   * 获取审批历史
   */
  async getReviewHistory(params?: ReviewListParams): Promise<{
    items: ReviewHistoryItem[];
    total: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());

    const url = `${this.baseUrl}/review-history?${queryParams.toString()}`;
    const response = await fetch(url);
    const result: ApiResponse<{ items: ReviewHistoryItem[]; total: number }> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取审批历史失败');
    }

    return result.data;
  }

  /**
   * 获取我的提交
   */
  async getMySubmissions(params?: ReviewListParams): Promise<{
    items: MySubmissionItem[];
    total: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());

    const url = `${this.baseUrl}/my-submissions?${queryParams.toString()}`;
    const response = await fetch(url);
    const result: ApiResponse<{ items: MySubmissionItem[]; total: number }> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取我的提交失败');
    }

    return result.data;
  }

  /**
   * 对比版本
   */
  async compareVersions(v1Id: string, v2Id: string): Promise<any> {
    const url = `${this.baseUrl}/versions/${v1Id}/compare/${v2Id}`;
    const response = await fetch(url);
    const result: ApiResponse<any> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '版本对比失败');
    }

    return result.data;
  }

  /**
   * 获取操作类型文本
   */
  static getActionText(action: string): string {
    const actionMap: Record<string, string> = {
      submit: '提交审核',
      approve: '审批通过',
      reject: '审批拒绝',
      obsolete: '作废',
      publish: '发布',
    };
    return actionMap[action] || action;
  }

  /**
   * 获取操作标签类型
   */
  static getActionType(action: string): '' | 'success' | 'warning' | 'danger' | 'info' {
    const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
      submit: 'info',
      approve: 'success',
      reject: 'danger',
      obsolete: 'danger',
      publish: 'success',
    };
    return typeMap[action] || '';
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
export const approvalWorkflowService = new ApprovalWorkflowService();
export default approvalWorkflowService;
