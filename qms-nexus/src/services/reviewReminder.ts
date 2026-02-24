/**
 * 文档复审提醒服务
 * 提供复审提醒相关的 API 调用
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// 类型定义
export interface PendingReviewDocument {
  id: string;
  document_id: string;
  document_title: string;
  document_code?: string;
  doc_type?: string;
  version_id: string;
  version_label: string;
  version_number: number;
  effective_date?: string;
  review_date?: string;
  days_until_review: number;
  urgency: 'low' | 'medium' | 'high' | 'overdue';
  kb_id: string;
}

export interface ReviewReminderStats {
  total_documents: number;
  overdue_count: number;
  urgent_count: number; // 7天内到期
  warning_count: number; // 30天内到期
  normal_count: number; // 30天以上
  completion_rate: number;
}

export interface ReviewReminderSettings {
  enabled: boolean;
  remind_before_days: number[]; // 提前提醒天数，如 [30, 7, 1]
  notify_channels: ('email' | 'sms' | 'in_app')[];
}

// API 响应格式
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

/**
 * 复审提醒服务类
 */
export class ReviewReminderService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/documents`;
  }

  /**
   * 获取待复审文档列表
   */
  async getPendingReviewDocuments(params?: {
    urgency?: 'low' | 'medium' | 'high' | 'overdue';
    page?: number;
    pageSize?: number;
  }): Promise<{
    items: PendingReviewDocument[];
    total: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.urgency) queryParams.append('urgency', params.urgency);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('page_size', params.pageSize.toString());

    const url = `${this.baseUrl}/pending-review?${queryParams.toString()}`;
    const response = await fetch(url);
    const result: ApiResponse<{ items: PendingReviewDocument[]; total: number }> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取待复审文档失败');
    }

    return result.data;
  }

  /**
   * 获取复审提醒统计
   */
  async getReviewReminderStats(): Promise<ReviewReminderStats> {
    const url = `${this.baseUrl}/review-stats`;
    const response = await fetch(url);
    const result: ApiResponse<ReviewReminderStats> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取复审统计失败');
    }

    return result.data;
  }

  /**
   * 发起复审（创建新版本）
   */
  async initiateReview(documentId: string, data: {
    changeSummary: string;
    changeDetails?: string;
    newReviewDate?: string;
  }): Promise<{ version_id: string }> {
    const url = `${this.baseUrl}/${documentId}/initiate-review`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const result: ApiResponse<{ version_id: string }> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '发起复审失败');
    }

    return result.data;
  }

  /**
   * 获取复审提醒设置
   */
  async getReminderSettings(): Promise<ReviewReminderSettings> {
    const url = `${this.baseUrl}/review-reminder-settings`;
    const response = await fetch(url);
    const result: ApiResponse<ReviewReminderSettings> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '获取提醒设置失败');
    }

    return result.data;
  }

  /**
   * 更新复审提醒设置
   */
  async updateReminderSettings(settings: ReviewReminderSettings): Promise<void> {
    const url = `${this.baseUrl}/review-reminder-settings`;
    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });

    const result: ApiResponse<void> = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '更新提醒设置失败');
    }
  }

  /**
   * 获取紧急程度文本
   */
  static getUrgencyText(urgency: string): string {
    const urgencyMap: Record<string, string> = {
      low: '正常',
      medium: '即将到期',
      high: '紧急',
      overdue: '已逾期',
    };
    return urgencyMap[urgency] || urgency;
  }

  /**
   * 获取紧急程度标签类型
   */
  static getUrgencyType(urgency: string): '' | 'success' | 'warning' | 'danger' | 'info' {
    const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
      low: 'success',
      medium: 'warning',
      high: 'danger',
      overdue: 'danger',
    };
    return typeMap[urgency] || '';
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
   * 计算剩余天数文本
   */
  static getDaysUntilReviewText(days: number): string {
    if (days < 0) {
      return `已逾期 ${Math.abs(days)} 天`;
    } else if (days === 0) {
      return '今天到期';
    } else {
      return `还有 ${days} 天`;
    }
  }
}

// 导出单例实例
export const reviewReminderService = new ReviewReminderService();
export default reviewReminderService;
