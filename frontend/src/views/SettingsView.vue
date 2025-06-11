<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { settingsService, type Notification } from '@/services/api';
import { ElMessage } from 'element-plus';

const form = ref<Notification>({
  telegram: {
    enabled: false,
    bot_token: '',
    chat_id: ''
  },
  feishu: {
    enabled: false,
    webhook: ''
  }
});

const isLoading = ref(true);

const fetchSettings = async () => {
  isLoading.value = true;
  try {
    const response = await settingsService.getNotificationSettings();
    form.value = response.data;
  } catch (error) {
    ElMessage.error('获取通知设置失败。');
    console.error(error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchSettings);

const handleSubmit = async () => {
  try {
    await settingsService.updateNotificationSettings(form.value);
    ElMessage.success('通知设置已更新！');
  } catch (error) {
    ElMessage.error('更新失败，请检查输入内容。');
    console.error(error);
  }
};
</script>

<template>
  <div class="settings-wrapper">
    <h1>通知设置</h1>
    <p class="description">在这里配置全局的默认通知方式。任务可以覆盖此处的默认设置。</p>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>飞书机器人</span>
            </div>
          </template>
          <el-form :model="form.feishu" label-width="120px" label-position="top">
            <el-form-item label="启用飞书通知">
              <el-switch v-model="form.feishu.enabled" />
            </el-form-item>
            <el-form-item label="Webhook URL">
              <el-input 
                v-model="form.feishu.webhook" 
                :disabled="!form.feishu.enabled"
                placeholder="请输入飞书机器人的 Webhook 地址"
                type="textarea"
                :rows="3"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Telegram Bot</span>
            </div>
          </template>
          <el-form :model="form.telegram" label-width="120px" label-position="top">
            <el-form-item label="启用 Telegram 通知">
              <el-switch v-model="form.telegram.enabled" />
            </el-form-item>
            <el-form-item label="Bot Token">
              <el-input 
                v-model="form.telegram.bot_token" 
                :disabled="!form.telegram.enabled"
                placeholder="请输入 Telegram Bot 的 Token"
              />
            </el-form-item>
            <el-form-item label="Chat ID">
              <el-input 
                v-model="form.telegram.chat_id" 
                :disabled="!form.telegram.enabled"
                placeholder="请输入接收消息的 Chat ID"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <div class="actions">
      <el-button type="primary" @click="handleSubmit">保存设置</el-button>
    </div>
  </div>
</template>

<style scoped>
.settings-wrapper {
  padding: 24px;
}
.description {
  color: #606266;
  margin-bottom: 20px;
}
.card-header {
  font-weight: bold;
}
.el-form-item {
  margin-bottom: 22px;
}
.actions {
  margin-top: 20px;
  text-align: right;
}
</style> 