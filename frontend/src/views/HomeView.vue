<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { taskService, settingsService, type Task, type Notification, type RuleInfo } from '@/services/api';
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
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '运行中' : '已禁用' }}</el-tag>
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
          <el-form-item>
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
          
          <el-form-item>
            <el-input
              v-model="customTemplate"
              type="textarea"
              :rows="10"
              placeholder="选择预设模板以预览，或选择自定义以编辑"
              :disabled="selectedPresetKey !== 'custom'"
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
</style>
