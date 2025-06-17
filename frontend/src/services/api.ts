import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Define the Task type to match the backend Pydantic model
export interface Task {
  name: string;
  url: string;
  frequency: string;
  rule: string;
  enabled: boolean;
  screenshot: boolean;
  notification_title?: string;
  notification: any; // You might want to type this more strictly
  // notification_template removed - only using AI-generated Python code
  ai_analysis_enabled: boolean;
  ai_description?: string;
  ai_extraction_rules?: Record<string, string> | null;
  ai_formatter_code?: string | null;
}

export interface TelegramNotification {
  enabled: boolean;
  bot_token?: string | null;
  chat_id?: string | null;
}

export interface FeishuNotification {
  enabled: boolean;
  webhook?: string | null;
}

export interface Notification {
  telegram: TelegramNotification;
  feishu: FeishuNotification;
}

export interface AIPreviewRequest {
  task_name: string;
  task_url: string;
  ai_description: string;
  page_content: string;
}

export interface AIPreviewResponse {
  success: boolean;
  title?: string;
  content?: string;
  summary?: string;
  extraction_rules?: Record<string, string>;
  formatter_code?: string;
  error?: string;
}

export interface RuleInfo {
  id: string;
  name: string;
  description: string;
  example: string;
  needs_value: boolean;
}

export interface ContentFetchRequest {
  name: string;
  url: string;
  rule: string;
}

export interface ContentFetchResponse {
  success: boolean;
  content: string;
  content_preview: string;
  content_length: number;
  error: string;
}

export const taskService = {
  getAllTasks() {
    return apiClient.get<Task[]>('/tasks/');
  },
  createTask(task: Task) {
    return apiClient.post<Task>('/tasks/', task);
  },
  updateTask(taskName: string, task: Task) {
    return apiClient.put<Task>(`/tasks/${taskName}`, task);
  },
  deleteTask(taskName: string) {
    return apiClient.delete(`/tasks/${taskName}`);
  }
};

export const logService = {
  getLogs() {
    return apiClient.get<string>('/logs/', {
      responseType: 'text' // Important to get raw text response
    });
  }
};

export const settingsService = {
  getNotificationSettings() {
    return apiClient.get<Notification>('/settings/notifications');
  },
  updateNotificationSettings(settings: Notification) {
    return apiClient.put<Notification>('/settings/notifications', settings);
  },
  // getNotificationPresets removed - only using AI-generated Python code
  getExtractionRules() {
    return apiClient.get<RuleInfo[]>('/settings/rules');
  }
};

export const aiService = {
  previewNotification(request: AIPreviewRequest) {
    return apiClient.post<AIPreviewResponse>('/ai/preview', request);
  },
  getSavedTemplate(taskName: string) {
    return apiClient.post<AIPreviewResponse>('/ai/get-saved-template', { task_name: taskName });
  }
};

export const contentService = {
  fetchContent(request: ContentFetchRequest) {
    return apiClient.post<ContentFetchResponse>('/content/fetch', request);
  }
};