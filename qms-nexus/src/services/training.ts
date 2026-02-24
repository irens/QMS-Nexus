/**
 * 培训/文档分发服务
 * 提供文档培训任务管理和确认功能
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// 类型定义
export interface TrainingTask {
  id: string;
  document_version_id: string;
  document_id: string;
  document_title: string;
  document_code?: string;
  version_label: string;
  version_number: number;
  distribution_type: 'read' | 'training' | 'acknowledge';
  status: 'pending' | 'completed';
  distributed_at: string;
  completed_at?: string;
  effective_date?: string;
  change_summary?: string;
}

export interface TrainingTaskListResponse {
  items: TrainingTask[];
  total: number;
  pending_count: number;
  completed_count: number;
}

export interface DistributionStatus {
  version_id: string;
  document_title: string;
  version_label: string;
  total_users: number;
  completed_count: number;
  pending_count: number;
  completion_rate: number;
  user_status: Array<{
    user_id: string;
    user_name: string;
    status: 'pending' | 'completed';
    completed_at?: string;
  }>;
}

export interface TrainingStats {
  total_tasks: number;
  pending_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  recent_completions: Array<{
    document_title: string;
    version_label: string;
    completed_at: string;
  }>;
}

// API 响应格式
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

/**
 * 培训服务类
 */
export class TrainingService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/documents`;
  }

  /**
   * 获取我的培训任务列表
   */
  async getMyTrainingTasks(params?: {
    status?: 'pending' | 'completed';
    page?: number;
    pageSize?: number;
  }): Promise<TrainingTaskListResponse> {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());

    const url = `${this.baseUrl}/my-training-tasks?${queryParams.toString()}`;
    const response = await fetch(url);
    const result: ApiResponse<TrainingTaskListResponse> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取培训任务失败');
    }

    return result.data;
  }

  /**
   * 确认阅读/培训完成
   */
  async acknowledgeTraining(distributionId: string): Promise<void> {
    const url = `${this.baseUrl}/distribution/${distributionId}/acknowledge`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '确认失败');
    }
  }

  /**
   * 获取文档分发状态
   */
  async getDistributionStatus(versionId: string): Promise<DistributionStatus> {
    const url = `${this.baseUrl}/versions/${versionId}/distribution`;
    const response = await fetch(url);
    const result: ApiResponse<DistributionStatus> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取分发状态失败');
    }

    return result.data;
  }

  /**
   * 获取培训统计
   */
  async getTrainingStats(): Promise<TrainingStats> {
    const url = `${this.baseUrl}/training-stats`;
    const response = await fetch(url);
    const result: ApiResponse<TrainingStats> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取培训统计失败');
    }

    return result.data;
  }

  /**
   * 获取分发类型文本
   */
  static getDistributionTypeText(type: string): string {
    const typeMap: Record<string, string> = {
      read: '阅读',
      training: '培训',
      acknowledge: '确认',
    };
    return typeMap[type] || type;
  }

  /**
   * 获取分发类型标签类型
   */
  static getDistributionTypeTag(type: string): '' | 'success' | 'warning' | 'danger' | 'info' {
    const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
      read: 'info',
      training: 'warning',
      acknowledge: 'success',
    };
    return typeMap[type] || '';
  }

  /**
   * 获取状态文本
   */
  static getStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      pending: '待完成',
      completed: '已完成',
    };
    return statusMap[status] || status;
  }

  /**
   * 获取状态标签类型
   */
  static getStatusType(status: string): '' | 'success' | 'warning' | 'danger' | 'info' {
    const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
      pending: 'warning',
      completed: 'success',
    };
    return typeMap[status] || '';
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
}

// 导出单例实例
export const trainingService = new TrainingService();
export default trainingService;
