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

// 多规则支持
const multiRulesEnabled = ref(false);
const rulesList = ref<Array<{id: number, ruleType: string, value: string}>>([]);

// Jinja2 template presets removed - only using AI-generated Python code
const customTemplate = ref('');

// 多规则管理函数
let nextRuleId = 1;

const addRule = () => {
  rulesList.value.push({
    id: nextRuleId++,
    ruleType: 'css',
    value: ''
  });
};

const removeRule = (id: number) => {
  const index = rulesList.value.findIndex(rule => rule.id === id);
  if (index > -1) {
    rulesList.value.splice(index, 1);
  }
};

const toggleMultiRules = () => {
  if (multiRulesEnabled.value) {
    // 切换到多规则模式，初始化一个规则
    if (rulesList.value.length === 0) {
      addRule();
    }
  } else {
    // 切换回单规则模式
    rulesList.value = [];
  }
};

// AI预览相关状态
const isGeneratingAI = ref(false);
const aiPreviewError = ref('');
const hasGeneratedNewAI = ref(false); // 标记是否刚刚生成了新的AI模板

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

// fetchPresets removed - only using AI-generated Python code

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
    // notification_template removed - only using AI-generated Python code
    ai_analysis_enabled: false,
    ai_description: '',
    ai_extraction_rules: null,
    ai_formatter_code: null,
    notification: {
      telegram: { enabled: false, bot_token: '', chat_id: '' },
      feishu: { enabled: false, webhook: '' }
    }
  };
  // Reset rule fields for create
  selectedRuleId.value = 'css';
  ruleValue.value = '';

  // 重置多规则状态
  multiRulesEnabled.value = false;
  rulesList.value = [];

  // Set initial state for create - only AI-generated templates
  customTemplate.value = '';

  // 重置内容获取状态
  fetchedContent.value = '';
  contentPreview.value = '';
  contentFetchError.value = '';
  aiPreviewError.value = '';
  hasGeneratedNewAI.value = false; // 重置AI生成标志

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
  if (task.rules && task.rules.length > 0) {
    // 多规则模式
    multiRulesEnabled.value = true;
    rulesList.value = task.rules.map((ruleStr, index) => {
      const ruleParts = ruleStr.split(':');
      const ruleType = ruleParts[0];
      const ruleValue = ruleParts.slice(1).join(':');
      return {
        id: index + 1,
        ruleType: ruleType,
        value: ruleValue
      };
    });
    nextRuleId = rulesList.value.length + 1;
    
    // 为向后兼容，也设置单规则字段
    selectedRuleId.value = 'css';
    ruleValue.value = '';
  } else {
    // 单规则模式（向后兼容）
    multiRulesEnabled.value = false;
    rulesList.value = [];
    
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
  }
  // --- End of rule parsing ---

  // 加载AI配置状态
  if (task.ai_analysis_enabled && task.ai_formatter_code) {
    // 如果有AI代码，加载已保存的模板预览
    customTemplate.value = '正在加载已保存的AI模板...';
    
    // 异步获取已保存的AI模板预览
    aiService.getSavedTemplate(task.name).then(response => {
      if (response.data.success && response.data.content) {
        customTemplate.value = response.data.content;
      } else {
        // 加载失败，只显示错误信息
        customTemplate.value = `❌ 加载已保存的AI模板失败: ${response.data.error || '未知错误'}`;
      }
    }).catch(error => {
      console.error('加载AI模板失败:', error);
      // 加载失败，只显示错误信息
      const errorMsg = error.response?.data?.error || '请求失败';
      customTemplate.value = `❌ 加载已保存的AI模板失败: ${errorMsg}`;
    });
  } else {
    customTemplate.value = '';
  }

  // 重置内容获取状态
  fetchedContent.value = '';
  contentPreview.value = '';
  contentFetchError.value = '';
  aiPreviewError.value = '';
  hasGeneratedNewAI.value = false; // 重置AI生成标志

  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!form.value.name) {
    ElMessage.error('任务名称不能为空');
    return;
  }
  
  // --- Rule composition logic ---
  if (multiRulesEnabled.value && rulesList.value.length > 0) {
    // 多规则模式
    form.value.rules = rulesList.value.map(rule => {
      const selectedRule = rules.value.find(r => r.id === rule.ruleType);
      if (selectedRule && selectedRule.needs_value) {
        return `${rule.ruleType}:${rule.value}`;
      } else {
        return rule.ruleType;
      }
    });
    // 保持向后兼容，设置第一个规则为主规则
    form.value.rule = form.value.rules[0];
  } else {
    // 单规则模式
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
    // 清空多规则字段
    form.value.rules = undefined;
  }
  // --- End of rule composition ---
  
  // Only AI-generated templates - no template field needed
  // form.notification_template removed

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
    hasGeneratedNewAI.value = false; // 重置AI生成标志
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
  let requestData: ContentFetchRequest;
  
  if (multiRulesEnabled.value && rulesList.value.length > 0) {
    // 多规则模式
    const rulesArray = rulesList.value.map(rule => {
      const selectedRule = rules.value.find(r => r.id === rule.ruleType);
      if (selectedRule && selectedRule.needs_value) {
        return `${rule.ruleType}:${rule.value}`;
      } else {
        return rule.ruleType;
      }
    });
    
    if (rulesArray.length === 0) {
      ElMessage.error('请至少添加一个提取规则');
      return;
    }
    
    requestData = {
      name: form.value.name,
      url: form.value.url,
      rules: rulesArray
    };
  } else {
    // 单规则模式
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
    
    requestData = {
      name: form.value.name,
      url: form.value.url,
      rule: rule
    };
  }

  isFetchingContent.value = true;
  contentFetchError.value = '';

  try {
    const response = await contentService.fetchContent(requestData);

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

      // 保存AI生成的提取规则和格式化代码
      if (response.data.extraction_rules && form.value) {
        form.value.ai_extraction_rules = response.data.extraction_rules;
      }

      if (response.data.formatter_code && form.value) {
        form.value.ai_formatter_code = response.data.formatter_code;
      }

      hasGeneratedNewAI.value = true; // 标记刚刚生成了新的AI模板
      ElMessage.success('AI模板生成成功！请点击"确定"按钮保存更改。');
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

// watch for selectedPresetKey removed - only using AI-generated templates

// Watcher to clear rule value when a rule that doesn't need a value is selected
watch(selectedRuleId, (newId) => {
  const selectedRule = rules.value.find(r => r.id === newId);
  if (selectedRule && !selectedRule.needs_value) {
    ruleValue.value = '';
  }
});

// Watch for multi-rules toggle
watch(multiRulesEnabled, (enabled) => {
  toggleMultiRules();
});

onMounted(() => {
  fetchTasks();
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
        <el-table-column label="提取规则">
          <template #default="{ row }">
            <div v-if="row.rules && row.rules.length > 0">
              <el-tag type="warning" size="small">多规则 ({{ row.rules.length }})</el-tag>
              <div style="font-size: 12px; color: #909399; margin-top: 2px;">
                {{ row.rules[0] }}{{ row.rules.length > 1 ? '...' : '' }}
              </div>
            </div>
            <div v-else>
              <el-tag type="info" size="small">单规则</el-tag>
              <div style="font-size: 12px; color: #909399; margin-top: 2px;">
                {{ row.rule }}
              </div>
            </div>
          </template>
        </el-table-column>
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
            <!-- 多规则开关 -->
            <div style="margin-bottom: 10px;">
              <el-switch 
                v-model="multiRulesEnabled" 
                active-text="多规则模式" 
                inactive-text="单规则模式"
                style="margin-right: 10px;"
              />
              <el-tooltip placement="top">
                <template #content>
                  <div>
                    多规则模式允许您提取页面的多个不同区域，<br />
                    AI将综合分析所有提取内容生成通知。<br />
                    例如：华为页面的标题区域和内容区域。
                  </div>
                </template>
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>

            <!-- 单规则模式 -->
            <div v-if="!multiRulesEnabled">
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
            </div>

            <!-- 多规则模式 -->
            <div v-if="multiRulesEnabled">
              <div v-for="(rule, index) in rulesList" :key="rule.id" class="multi-rule-item">
                <div class="rule-row">
                  <el-input 
                    v-model="rule.value" 
                    :placeholder="`提取规则 ${index + 1}`" 
                    :disabled="!rules.find(r => r.id === rule.ruleType)?.needs_value"
                    style="flex: 1;"
                  >
                    <template #prepend>
                      <el-select v-model="rule.ruleType" style="width: 130px">
                        <el-option
                          v-for="ruleOption in rules"
                          :key="ruleOption.id"
                          :label="ruleOption.name"
                          :value="ruleOption.id"
                        />
                      </el-select>
                    </template>
                  </el-input>
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="removeRule(rule.id)"
                    :disabled="rulesList.length <= 1"
                    style="margin-left: 8px;"
                  >
                    删除
                  </el-button>
                </div>
                <div class="rule-description" v-if="rules.find(r => r.id === rule.ruleType)">
                  <p>
                    {{ rules.find(r => r.id === rule.ruleType)?.description }}<br>
                    <em>{{ rules.find(r => r.id === rule.ruleType)?.example }}</em>
                  </p>
                </div>
              </div>
              
              <el-button 
                type="primary" 
                size="small" 
                @click="addRule"
                style="margin-top: 10px;"
              >
                + 添加规则
              </el-button>
              
              <div class="multi-rule-help">
                <el-alert
                  title="多规则使用提示"
                  type="info"
                  :closable="false"
                  show-icon
                  style="margin-top: 10px;"
                >
                  <ul>
                    <li>每个规则提取页面的不同区域</li>
                    <li>AI将合并所有区域的内容进行分析</li>
                    <li>适用于复杂页面的精确数据提取</li>
                    <li>例如：标题区域 + 内容区域 + 链接区域</li>
                  </ul>
                </el-alert>
              </div>
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
              <div v-if="hasGeneratedNewAI" style="margin-top: 8px; color: #e6a23c; font-size: 12px;">
                ⚠️ 已生成新的AI模板，请点击底部"确定"按钮保存更改
              </div>
            </div>
          </el-form-item>
          <!-- Jinja2 template selector removed - only using AI-generated Python code -->
          <el-form-item v-if="!form.ai_analysis_enabled">
            <template #label>
              <span>
                通知模式
                <el-tooltip placement="top">
                  <template #content>
                    <div>
                      请启用AI智能通知以获得最佳体验。<br />
                      AI会根据您的监控描述自动生成通知内容。<br />
                      传统模板功能已移除，建议使用AI智能通知。
                    </div>
                  </template>
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </template>
            <el-alert
              title="建议启用AI智能通知"
              type="info"
              description="传统Jinja2模板已移除，请启用AI智能通知获得更好的体验。"
              show-icon
              :closable="false">
            </el-alert>
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

/* 多规则样式 */
.multi-rule-item {
  margin-bottom: 15px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafafa;
}

.rule-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.multi-rule-help {
  margin-top: 15px;
}

.multi-rule-help .el-alert ul {
  margin: 0;
  padding-left: 20px;
}

.multi-rule-help .el-alert li {
  margin: 4px 0;
}
</style>
