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
  notification_template?: string;
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
  getNotificationPresets() {
    return apiClient.get<Record<string, string>>('/settings/notifications/presets');
  }
}; 