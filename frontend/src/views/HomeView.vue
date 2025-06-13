<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { taskService, settingsService, aiService, contentService, type Task, type Notification, type RuleInfo, type AIPreviewRequest, type ContentFetchRequest } from '@/services/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import { QuestionFilled } from '@element-plus/icons-vue';

const tasks = ref<Task[]>([]);
const isLoading = ref(true);

const dialogVisible = ref(false);
const isEditMode = ref(false);
const form = ref<Partial<Task>>({});

// Rule selection state
const rules = ref<RuleInfo[]>([]);
const selectedRuleId = ref('css');
const ruleValue = ref('');

const notificationPresets = ref<Record<string, string>>({});
const selectedPresetKey = ref('');
const customTemplate = ref('');

// AI预览相关状态
const isGeneratingAI = ref(false);
const aiPreviewError = ref('');

// 内容获取相关状态
const isFetchingContent = ref(false);
const fetchedContent = ref('');
const contentPreview = ref('');
const contentFetchError = ref('');

const dialogTitle = computed(() => (isEditMode.value ? '编辑任务' : '新建任务'));

const fetchTasks = async () => {
  try {
    isLoading.value = true;
    const response = await taskService.getAllTasks();
    tasks.value = response.data;
  } catch (error) {
    ElMessage.error('无法加载任务列表');
  } finally {
    isLoading.value = false;
  }
};

const fetchRules = async () => {
  try {
    const response = await settingsService.getExtractionRules();
    rules.value = response.data;
  } catch (error) {
    ElMessage.error('无法加载提取规则列表');
  }
};

const fetchPresets = async () => {
  try {
    const response = await settingsService.getNotificationPresets();
    notificationPresets.value = response.data;
  } catch (error) {
    ElMessage.error('无法加载通知模板预设');
  }
};

const openCreateDialog = () => {
  isEditMode.value = false;
  form.value = {
    name: '',
    url: '',
    frequency: '10m',
    rule: 'css:',
    enabled: true,
    screenshot: false,
    notification_title: '',
    notification_template: 'default',
    ai_analysis_enabled: false,
    ai_description: '',
    ai_extraction_rules: null,
    notification: {
      telegram: { enabled: false, bot_token: '', chat_id: '' },
      feishu: { enabled: false, webhook: '' }
    }
  };
  // Reset rule fields for create
  selectedRuleId.value = 'css';
  ruleValue.value = '';

  // Set initial state for create
  selectedPresetKey.value = 'default';
  customTemplate.value = notificationPresets.value['default'] || '';

  // 重置内容获取状态
  fetchedContent.value = '';
  contentPreview.value = '';
  contentFetchError.value = '';
  aiPreviewError.value = '';

  dialogVisible.value = true;
};

const openEditDialog = async (task: Task) => {
  isEditMode.value = true;
  form.value = { 
    ...task,
    notification: task.notification || { 
      telegram: { enabled: false, bot_token: '', chat_id: '' },
      feishu: { enabled: false, webhook: '' }
    }
  };

  // --- Rule parsing logic ---
  const ruleParts = (task.rule || 'css:').split(':');
  const ruleType = ruleParts[0];
  const currentRule = rules.value.find(r => r.id === ruleType);

  if (currentRule) {
    selectedRuleId.value = currentRule.id;
    if (currentRule.needs_value) {
      ruleValue.value = ruleParts.slice(1).join(':');
    } else {
      ruleValue.value = '';
    }
  } else {
    // Fallback for unknown rule
    selectedRuleId.value = 'css';
    ruleValue.value = task.rule || '';
  }
  // --- End of rule parsing ---

  // Ensure presets are loaded before setting the state
  if (Object.keys(notificationPresets.value).length === 0) {
    await fetchPresets();
  }

  const templateValue = task.notification_template || 'default';

  if (notificationPresets.value[templateValue]) {
    selectedPresetKey.value = templateValue;
    customTemplate.value = notificationPresets.value[templateValue];
  } else {
    selectedPresetKey.value = 'custom';
    customTemplate.value = templateValue;
  }
  
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!form.value.name) {
    ElMessage.error('任务名称不能为空');
    return;
  }
  
  // --- Rule composition logic ---
  const selectedRule = rules.value.find(r => r.id === selectedRuleId.value);
  if (selectedRule) {
    if (selectedRule.needs_value) {
      form.value.rule = `${selectedRule.id}:${ruleValue.value}`;
    } else {
      form.value.rule = selectedRule.id;
    }
  } else {
    form.value.rule = ruleValue.value; // Fallback
  }
  // --- End of rule composition ---
  
  // Set the correct template value before submitting
  if (selectedPresetKey.value === 'custom') {
    form.value.notification_template = customTemplate.value;
  } else {
    form.value.notification_template = selectedPresetKey.value;
  }

  // Data cleaning before submission
  const payload = { ...form.value };
  if (payload.notification) {
    const feishuEnabled = payload.notification.feishu?.enabled;
    const telegramEnabled = payload.notification.telegram?.enabled;

    if (!feishuEnabled && !telegramEnabled) {
      // If no notification method is enabled, set the whole notification object to null
      payload.notification = null;
    } else {
      if (feishuEnabled && !payload.notification.feishu?.webhook) {
         payload.notification.feishu.enabled = false;
      }
      if (telegramEnabled && (!payload.notification.telegram?.bot_token || !payload.notification.telegram?.chat_id)) {
        payload.notification.telegram.enabled = false;
      }
      // If after cleaning, both are disabled, set to null
      if (!payload.notification.feishu?.enabled && !payload.notification.telegram?.enabled) {
        payload.notification = null;
      }
    }
  }

  try {
    if (isEditMode.value && payload.name) {
      await taskService.updateTask(payload.name, payload as Task);
      ElMessage.success('任务更新成功');
    } else {
      await taskService.createTask(payload as Task);
      ElMessage.success('任务创建成功');
    }
    dialogVisible.value = false;
    fetchTasks();
  } catch (error: any) {
    const detail = error.response?.data?.detail || '操作失败';
    ElMessage.error(`错误: ${detail}`);
  }
};

const handleDelete = (taskName: string) => {
  ElMessageBox.confirm('确定要删除这个任务吗?', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await taskService.deleteTask(taskName);
      ElMessage.success('任务删除成功');
      fetchTasks();
    } catch (error) {
      ElMessage.error('删除任务失败');
    }
  });
};

const fetchPageContent = async () => {
  if (!form.value.name || !form.value.url) {
    ElMessage.error('请先填写任务名称和URL');
    return;
  }

  // 构建提取规则
  const selectedRule = rules.value.find(r => r.id === selectedRuleId.value);
  let rule = '';
  if (selectedRule) {
    if (selectedRule.needs_value) {
      rule = `${selectedRule.id}:${ruleValue.value}`;
    } else {
      rule = selectedRule.id;
    }
  } else {
    rule = ruleValue.value;
  }

  if (!rule) {
    ElMessage.error('请先设置提取规则');
    return;
  }

  isFetchingContent.value = true;
  contentFetchError.value = '';

  try {
    const request: ContentFetchRequest = {
      name: form.value.name,
      url: form.value.url,
      rule: rule
    };

    const response = await contentService.fetchContent(request);

    if (response.data.success && response.data.content) {
      fetchedContent.value = response.data.content;
      contentPreview.value = response.data.content_preview;
      ElMessage.success(`页面内容获取成功！(${response.data.content_length} 字符)`);
    } else {
      contentFetchError.value = response.data.error || '获取页面内容失败';
      ElMessage.error(contentFetchError.value);
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error || '获取页面内容请求失败';
    contentFetchError.value = errorMsg;
    ElMessage.error(errorMsg);
  } finally {
    isFetchingContent.value = false;
  }
};

const generateAIPreview = async () => {
  if (!form.value.name || !form.value.url || !form.value.ai_description) {
    ElMessage.error('请先填写任务名称、URL和监控描述');
    return;
  }

  if (!fetchedContent.value) {
    ElMessage.error('请先获取页面内容');
    return;
  }

  isGeneratingAI.value = true;
  aiPreviewError.value = '';

  try {
    const request: AIPreviewRequest = {
      task_name: form.value.name,
      task_url: form.value.url,
      ai_description: form.value.ai_description,
      page_content: fetchedContent.value
    };

    const response = await aiService.previewNotification(request);

    if (response.data.success && response.data.content) {
      customTemplate.value = response.data.content;
      selectedPresetKey.value = 'custom';  // 自动切换到自定义模板

      // 保存AI生成的提取规则
      if (response.data.extraction_rules && form.value) {
        form.value.ai_extraction_rules = response.data.extraction_rules;
      }

      ElMessage.success('AI模板生成成功！');
    } else {
      aiPreviewError.value = response.data.error || 'AI分析失败';
      ElMessage.error(aiPreviewError.value);
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error || 'AI预览请求失败';
    aiPreviewError.value = errorMsg;
    ElMessage.error(errorMsg);
  } finally {
    isGeneratingAI.value = false;
  }
};

watch(selectedPresetKey, (newKey) => {
  if (newKey && newKey !== 'custom' && notificationPresets.value[newKey]) {
    customTemplate.value = notificationPresets.value[newKey];
  } else if (newKey === 'custom') {
    // Do not clear the text area when user wants to customize
  } else {
    // Cleared or invalid selection, maybe reset custom template
    customTemplate.value = '';
  }
});

// Watcher to clear rule value when a rule that doesn't need a value is selected
watch(selectedRuleId, (newId) => {
  const selectedRule = rules.value.find(r => r.id === newId);
  if (selectedRule && !selectedRule.needs_value) {
    ruleValue.value = '';
  }
});

onMounted(() => {
  fetchTasks();
  fetchPresets();
  fetchRules();
});
</script>

<template>
  <el-container class="home-view">
    <el-header>
      <h1>网页内容监控</h1>
      <el-button type="primary" @click="openCreateDialog">新建任务</el-button>
    </el-header>
    <el-main>
      <el-table :data="tasks" v-loading="isLoading" stripe>
        <el-table-column prop="name" label="任务名称" width="180" />
        <el-table-column prop="url" label="URL" />
        <el-table-column prop="frequency" label="频率" width="80" />
        <el-table-column prop="rule" label="提取规则" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <div>
              <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '运行中' : '已禁用' }}</el-tag>
              <el-tag v-if="row.ai_analysis_enabled" type="warning" size="small" style="margin-left: 4px;">AI</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="dialogVisible" :title="dialogTitle" width="50%">
        <el-form v-if="form" :model="form" label-width="120px">
          <el-form-item label="任务名称">
            <el-input v-model="form.name" :disabled="isEditMode" />
          </el-form-item>
          <el-form-item label="URL">
            <el-input v-model="form.url" />
          </el-form-item>
          <el-form-item label="监控频率">
            <el-input v-model="form.frequency" placeholder="例如: 10m, 1h" />
          </el-form-item>
          <el-form-item label="提取规则">
            <el-input v-model="ruleValue" placeholder="请输入规则值" :disabled="!rules.find(r => r.id === selectedRuleId)?.needs_value">
              <template #prepend>
                <el-select v-model="selectedRuleId" style="width: 130px">
                  <el-option
                    v-for="rule in rules"
                    :key="rule.id"
                    :label="rule.name"
                    :value="rule.id"
                  />
                </el-select>
              </template>
            </el-input>
            <div class="rule-description">
              <p v-if="rules.find(r => r.id === selectedRuleId)">
                {{ rules.find(r => r.id === selectedRuleId)?.description }}<br>
                <em>{{ rules.find(r => r.id === selectedRuleId)?.example }}</em>
              </p>
            </div>
          </el-form-item>
          <el-form-item label="通知标题 (可选)">
            <el-input v-model="form.notification_title" />
          </el-form-item>
          <el-form-item label="启用任务">
            <el-switch v-model="form.enabled" />
          </el-form-item>
          <el-form-item label="开启截图">
            <el-switch v-model="form.screenshot" />
          </el-form-item>

          <el-divider>AI智能通知</el-divider>

          <el-form-item>
            <template #label>
              <span>
                启用AI智能通知
                <el-tooltip placement="top">
                  <template #content>
                    <div>
                      启用后，AI将分析内容变化并生成简洁美观的通知，<br />
                      而不是发送原始的HTML内容摘要。<br />
                      需要配置OPENAI_API_KEY环境变量。
                    </div>
                  </template>
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </template>
            <el-switch v-model="form.ai_analysis_enabled" />
          </el-form-item>

          <el-form-item
            v-if="form.ai_analysis_enabled"
            label="监控描述"
          >
            <el-input
              v-model="form.ai_description"
              type="textarea"
              :rows="3"
              placeholder="请描述你想从变化中提取什么信息，例如：我想监控版本号变化、下载链接更新、支持规范变化"
            />
            <div class="form-item-help">
              <p>用自然语言描述你关心的变化内容，AI将据此生成针对性的通知。</p>
            </div>

            <!-- 获取页面内容步骤 -->
            <div style="margin-top: 15px;">
              <div style="margin-bottom: 10px;">
                <span style="font-weight: 500; color: #409EFF;">步骤1: 获取页面内容</span>
              </div>
              <el-button
                type="info"
                :loading="isFetchingContent"
                @click="fetchPageContent"
                :disabled="!form.name || !form.url"
                style="margin-right: 10px;"
              >
                <span v-if="isFetchingContent">获取中...</span>
                <span v-else>📄 获取页面内容</span>
              </el-button>

              <!-- 内容预览 -->
              <div v-if="contentPreview" style="margin-top: 10px; padding: 10px; background-color: #f5f7fa; border-radius: 4px; border: 1px solid #dcdfe6;">
                <div style="font-size: 12px; color: #909399; margin-bottom: 5px;">内容预览:</div>
                <div style="font-size: 13px; color: #606266;">{{ contentPreview }}</div>
              </div>

              <div v-if="contentFetchError" class="ai-error-message">
                ❌ {{ contentFetchError }}
              </div>
            </div>

            <!-- 生成AI模板步骤 -->
            <div style="margin-top: 15px;">
              <div style="margin-bottom: 10px;">
                <span style="font-weight: 500; color: #409EFF;">步骤2: 生成AI模板</span>
              </div>
              <el-button
                type="primary"
                :loading="isGeneratingAI"
                @click="generateAIPreview"
                :disabled="!form.name || !form.url || !form.ai_description || !fetchedContent"
              >
                <span v-if="isGeneratingAI">生成中...</span>
                <span v-else>🤖 生成AI模板预览</span>
              </el-button>
              <div v-if="aiPreviewError" class="ai-error-message">
                ❌ {{ aiPreviewError }}
              </div>
            </div>
          </el-form-item>
          <el-form-item v-if="!form.ai_analysis_enabled">
            <template #label>
              <span>
                通知模板
                <el-tooltip placement="top">
                  <template #content>
                    <div>
                      选择预设模板，或选择"自定义模板"并编辑内容。<br />
                      模板引擎已升级为 Jinja2，支持条件判断。<br />
                      例如: <code>{% raw %}{% if screenshot_url %} [查看截图](&#123;&#123; screenshot_url &#125;&#125;) {% endif %}{% endraw %}</code>
                    </div>
                  </template>
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </template>
            <el-select v-model="selectedPresetKey" placeholder="请选择或自定义模板" style="width: 100%;">
              <el-option
                v-for="(value, key) in notificationPresets"
                :key="key"
                :label="key"
                :value="key"
              />
              <el-option label="-- 自定义模板 --" value="custom" />
            </el-select>
          </el-form-item>

          <el-form-item v-if="!form.ai_analysis_enabled">
            <el-input
              v-model="customTemplate"
              type="textarea"
              :rows="10"
              placeholder="选择预设模板以预览，或选择自定义以编辑"
              :disabled="selectedPresetKey !== 'custom'"
            />
          </el-form-item>

          <el-form-item v-if="form.ai_analysis_enabled">
            <template #label>
              <span>
                AI生成的通知模板
                <el-tooltip placement="top">
                  <template #content>
                    <div>
                      这里显示AI根据你的监控描述生成的通知模板。<br />
                      你可以查看和编辑AI生成的内容。<br />
                      如果AI分析失败，将使用这里的内容作为通知模板。
                    </div>
                  </template>
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </template>
            <el-input
              v-model="customTemplate"
              type="textarea"
              :rows="8"
              placeholder="AI将根据你的监控描述自动生成通知模板..."
            />
          </el-form-item>

          <el-divider>通知设置 (留空则使用全局默认)</el-divider>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item>
                <div class="form-item-flex-container">
                  <span>启用飞书通知</span>
                  <el-switch v-model="form.notification.feishu.enabled" />
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item>
                <div class="form-item-flex-container">
                  <span>启用Telegram通知</span>
                  <el-switch v-model="form.notification.telegram.enabled" />
                </div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item v-if="form.notification.feishu.enabled" label="飞书 Webhook">
            <el-input v-model="form.notification.feishu.webhook" placeholder="此任务专属的飞书 Webhook" />
          </el-form-item>

          <div v-if="form.notification.telegram.enabled">
            <el-form-item label="Telegram Token">
              <el-input v-model="form.notification.telegram.bot_token" placeholder="此任务专属的 Bot Token" />
            </el-form-item>
            <el-form-item label="Telegram Chat ID">
              <el-input v-model="form.notification.telegram.chat_id" placeholder="此任务专属的 Chat ID" />
            </el-form-item>
          </div>

        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="handleSubmit">确定</el-button>
          </span>
        </template>
      </el-dialog>
    </el-main>
  </el-container>
</template>

<style scoped>
.home-view {
  padding: 1rem;
}
.el-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.el-table .el-tag {
  cursor: default;
}
.el-table .el-button {
  margin-right: 5px;
}
.el-table-column {
  word-break: break-all;
}
.form-item-help {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}
.form-item-help p {
  margin: 0;
}
.form-item-help code {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 4px;
}
.form-item-flex-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.rule-description {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}
.ai-error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 8px;
  padding: 8px;
  background-color: #fef0f0;
  border-radius: 4px;
  border: 1px solid #fbc4c4;
}
</style>
