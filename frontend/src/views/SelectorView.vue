<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage } from 'element-plus';

// 类型定义
interface SelectorStrategy {
  name: string;
  css: string;
  xpath: string;
  description: string;
}

interface SelectorResult {
  css_selector: string;
  css_options?: string[];
  xpath: string;
  xpath_options?: string[];
  recommended_type: string;
  mode_recommend: string;
  example_text: string;
  tag: string;
  timestamp: number;
  intent?: string;
  strategies?: SelectorStrategy[];
  description?: string;
  confidence?: number;
  type_analysis?: {
    [key: string]: {
      score: number;
      reason: string;
    };
  };
}

// 响应式状态
const router = useRouter();
const url = ref('https://news.ycombinator.com');
const isLoading = ref(false);
const sessionId = ref('');
const selectorResult = ref<SelectorResult | null>(null);
const iframeUrl = ref('');
const errorMessage = ref('');

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 消息监听器引用
let messageListener: ((event: MessageEvent) => void) | null = null;

// 加载页面
const loadPage = async () => {
  if (!url.value.trim()) {
    ElMessage.error('请输入有效的URL');
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';
  selectorResult.value = null;

  try {
    // 创建选择器会话
    const response = await axios.post(`${API_BASE_URL}/api/selector/load`, {
      url: url.value
    });

    sessionId.value = response.data.session_id;

    // 构建iframe URL
    iframeUrl.value = `${API_BASE_URL}/api/selector/render/${sessionId.value}`;

    ElMessage.success('页面加载成功，请点击要监控的元素');
  } catch (error: any) {
    console.error('Error loading page:', error);
    errorMessage.value = error.response?.data?.detail || '页面加载失败';
    ElMessage.error(errorMessage.value);
  } finally {
    isLoading.value = false;
  }
};

// 重新开始
const restart = () => {
  url.value = '';
  sessionId.value = '';
  selectorResult.value = null;
  iframeUrl.value = '';
  errorMessage.value = '';
};

// 清理选择结果但保持iframe
const clearResult = () => {
  selectorResult.value = null;
};

// 复制到剪贴板
const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success('已复制到剪贴板');
  } catch (error) {
    console.error('复制失败:', error);
    ElMessage.error('复制失败');
  }
};

// 测试选择器
const testSelector = (selector: string, type: 'css' | 'xpath') => {
  const testCode = type === 'css'
    ? `document.querySelectorAll('${selector.replace(/'/g, "\\'")}').length`
    : `document.evaluate('${selector.replace(/'/g, "\\'")}', document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotLength`;

  ElMessage.info(`请在目标网站的控制台中运行: ${testCode}`);
  copyToClipboard(testCode);
};

// 使用选择器创建任务
const createTask = () => {
  if (!selectorResult.value) return;

  // 跳转到任务管理页面，并传递选择器信息
  router.push({
    path: '/',
    query: {
      newTask: 'true',
      url: url.value,
      selector: selectorResult.value.css_selector,
      mode: selectorResult.value.mode_recommend
    }
  });
};

// 处理来自iframe的消息
const handleMessage = (event: MessageEvent) => {
  console.log('Received message from iframe:', event);
  console.log('Message data:', event.data);
  console.log('Message origin:', event.origin);

  if (event.data?.type === 'SELECTOR_RESULT') {
    selectorResult.value = event.data.data;
    ElMessage.success('元素选择成功！');
    console.log('Received selector result:', event.data.data);
  } else {
    console.log('Message type not recognized:', event.data?.type);
  }
};

// 获取模式标签类型
const getModeTagType = (mode: string) => {
  switch (mode) {
    case 'latest': return 'success';
    case 'fixed': return 'info';
    case 'list': return 'warning';
    default: return 'info';
  }
};

// 获取模式显示名称
const getModeDisplayName = (mode: string) => {
  switch (mode) {
    case 'latest': return '最新内容监控';
    case 'fixed': return '固定位置监控';
    case 'list': return '列表监控';
    default: return mode === 'latest' ? '最新内容' : mode === 'list' ? '列表项' : '固定区域';
  }
};

// 获取模式描述
const getModeDescription = (intent: string) => {
  switch (intent) {
    case 'latest': return '将监控列表中第一个位置的内容，无论内容如何更新';
    case 'fixed': return '将监控当前选中的这个具体元素的内容变化';
    case 'list': return '将监控列表中所有项目的变化';
    default: return '';
  }
};

// 获取选择器类型标签类型
const getSelectorTypeTagType = (type: string) => {
  switch (type) {
    case 'css': return 'success';
    case 'xpath': return 'warning';
    default: return 'info';
  }
};

// 获取选择器类型显示名称
const getSelectorTypeDisplayName = (type: string) => {
  switch (type) {
    case 'css': return 'CSS选择器';
    case 'xpath': return 'XPath';
    default: return type;
  }
};

// 测试选择器（支持CSS和XPath）
const testSelectorExtended = (selector: string, type: 'css' | 'xpath') => {
  let testCode = '';
  switch (type) {
    case 'css':
      testCode = `document.querySelectorAll('${selector.replace(/'/g, "\\'")}').length`;
      break;
    case 'xpath':
      testCode = `document.evaluate('${selector.replace(/'/g, "\\'")}', document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotLength`;
      break;
  }

  ElMessage.info(`请在目标网站的控制台中运行: ${testCode}`);
  copyToClipboard(testCode);
};

// 生命周期钩子
onMounted(() => {
  messageListener = handleMessage;
  window.addEventListener('message', messageListener);
});

onUnmounted(() => {
  if (messageListener) {
    window.removeEventListener('message', messageListener);
  }

  // 清理会话
  if (sessionId.value) {
    axios.delete(`${API_BASE_URL}/api/selector/session/${sessionId.value}`)
      .catch(console.error);
  }
});
</script>

<template>
  <div class="selector-view">
    <el-container>
      <!-- 头部 -->
      <el-header class="header">
        <h1>可视化元素选择器</h1>
        <p class="subtitle">通过点击页面元素自动生成CSS选择器和XPath</p>
      </el-header>

      <el-container>
        <!-- 左侧主内容区 -->
        <el-main class="main-content">
          <!-- URL输入区域 -->
          <el-card v-if="!iframeUrl" class="url-card">
            <template #header>
              <div class="card-header">
                <span>输入目标网页URL</span>
              </div>
            </template>

            <div class="url-input-section">
              <el-input
                v-model="url"
                placeholder="例如: https://news.ycombinator.com"
                size="large"
                :disabled="isLoading"
                @keyup.enter="loadPage"
              >
                <template #prepend>
                  <el-icon><span>🔗</span></el-icon>
                </template>
              </el-input>

              <el-button
                type="primary"
                size="large"
                :loading="isLoading"
                @click="loadPage"
                class="load-button"
              >
                {{ isLoading ? '加载中...' : '加载页面' }}
              </el-button>
            </div>

            <div class="tips">
              <el-alert
                title="使用提示"
                type="info"
                :closable="false"
                show-icon
              >
                <ul>
                  <li>输入要监控的网页URL</li>
                  <li>页面加载后，点击要监控的元素</li>
                  <li>系统将自动生成CSS选择器和XPath</li>
                  <li>支持HTTPS网站的安全访问</li>
                </ul>
              </el-alert>
            </div>
          </el-card>

          <!-- iframe展示区域 -->
          <el-card v-if="iframeUrl" class="iframe-card">
            <template #header>
              <div class="card-header">
                <span>{{ url }}</span>
                <el-button size="small" @click="restart">重新开始</el-button>
              </div>
            </template>

            <div class="iframe-container">
              <iframe
                :src="iframeUrl"
                frameborder="0"
                class="target-iframe"
                title="目标网页"
              ></iframe>
            </div>

            <div class="iframe-tips">
              <el-alert
                title="请点击要监控的页面元素"
                type="warning"
                :closable="false"
                show-icon
              >
                点击页面中的任意元素，系统将自动生成对应的选择器规则
              </el-alert>
            </div>
          </el-card>

          <!-- 错误信息 -->
          <el-card v-if="errorMessage" class="error-card">
            <el-alert
              :title="errorMessage"
              type="error"
              show-icon
              :closable="false"
            />
            <div class="error-actions">
              <el-button @click="restart">重新开始</el-button>
            </div>
          </el-card>
        </el-main>

        <!-- 右侧结果展示区 -->
        <el-aside v-if="selectorResult" width="400px" class="result-sidebar">
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>选择器结果</span>
                <el-button size="small" @click="clearResult">继续选择</el-button>
              </div>
            </template>

            <el-descriptions :column="1" border>
              <el-descriptions-item label="元素标签">
                <el-tag>{{ selectorResult.tag }}</el-tag>
              </el-descriptions-item>

              <!-- AI推荐的选择器类型 -->
              <el-descriptions-item label="AI推荐类型" v-if="selectorResult.recommended_type">
                <el-tag :type="getSelectorTypeTagType(selectorResult.recommended_type)" size="large">
                  🤖 {{ getSelectorTypeDisplayName(selectorResult.recommended_type) }}
                </el-tag>
                <div v-if="selectorResult.description" class="recommendation-description">
                  {{ selectorResult.description }}
                </div>
              </el-descriptions-item>

              <!-- 所有选择器类型 -->
              <el-descriptions-item label="CSS选择器">
                <div class="selector-item">
                  <div class="selector-header">
                    <el-tag
                      :type="selectorResult.recommended_type === 'css' ? 'success' : 'info'"
                      size="small"
                    >
                      {{ selectorResult.recommended_type === 'css' ? '🌟 推荐' : 'CSS' }}
                    </el-tag>
                    <div class="selector-score" v-if="selectorResult.type_analysis?.css">
                      评分: {{ selectorResult.type_analysis.css.score }}
                    </div>
                  </div>
                  <el-input
                    :value="selectorResult.css_selector"
                    readonly
                    type="textarea"
                    :rows="2"
                  />
                  <div class="selector-actions">
                    <el-button size="small" @click="copyToClipboard(selectorResult.css_selector)">复制</el-button>
                    <el-button size="small" @click="testSelectorExtended(selectorResult.css_selector, 'css')">测试</el-button>
                  </div>
                  <div v-if="selectorResult.type_analysis?.css?.reason" class="selector-reason">
                    {{ selectorResult.type_analysis.css.reason }}
                  </div>
                </div>
              </el-descriptions-item>

              <el-descriptions-item label="XPath">
                <div class="selector-item">
                  <div class="selector-header">
                    <el-tag
                      :type="selectorResult.recommended_type === 'xpath' ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ selectorResult.recommended_type === 'xpath' ? '🌟 推荐' : 'XPath' }}
                    </el-tag>
                    <div class="selector-score" v-if="selectorResult.type_analysis?.xpath">
                      评分: {{ selectorResult.type_analysis.xpath.score }}
                    </div>
                  </div>
                  <el-input
                    :value="selectorResult.xpath"
                    readonly
                    type="textarea"
                    :rows="2"
                  />
                  <div class="selector-actions">
                    <el-button size="small" @click="copyToClipboard(selectorResult.xpath)">复制</el-button>
                    <el-button size="small" @click="testSelectorExtended(selectorResult.xpath, 'xpath')">测试</el-button>
                  </div>
                  <div v-if="selectorResult.type_analysis?.xpath?.reason" class="selector-reason">
                    {{ selectorResult.type_analysis.xpath.reason }}
                  </div>
                </div>
              </el-descriptions-item>



              <el-descriptions-item label="监控模式">
                <el-tag :type="getModeTagType(selectorResult.mode_recommend)">
                  {{ getModeDisplayName(selectorResult.mode_recommend) }}
                </el-tag>
                <div v-if="selectorResult.intent" class="mode-description">
                  {{ getModeDescription(selectorResult.intent) }}
                </div>
              </el-descriptions-item>

              <el-descriptions-item label="示例文本" v-if="selectorResult.example_text">
                <div class="example-text">{{ selectorResult.example_text }}</div>
              </el-descriptions-item>
            </el-descriptions>

            <div class="result-actions">
              <el-button type="primary" @click="createTask">
                创建监控任务
              </el-button>
              <el-button @click="clearResult">继续选择</el-button>
              <el-button @click="restart">重新开始</el-button>
            </div>
          </el-card>
        </el-aside>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.selector-view {
  height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 20px;
}

.header h1 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
}

.subtitle {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.main-content {
  padding: 20px;
}

.url-card, .iframe-card, .error-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.url-input-section {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.url-input-section .el-input {
  flex: 1;
}

.load-button {
  min-width: 120px;
}

.tips ul {
  margin: 0;
  padding-left: 20px;
}

.tips li {
  margin-bottom: 4px;
}

.iframe-container {
  height: 600px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.target-iframe {
  width: 100%;
  height: 100%;
}

.iframe-tips {
  margin-top: 12px;
}

.result-sidebar {
  padding: 20px;
  background: white;
  border-left: 1px solid #e4e7ed;
}

.result-card {
  height: fit-content;
}

.example-text {
  max-height: 100px;
  overflow-y: auto;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
}

.result-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.error-actions {
  margin-top: 16px;
  text-align: center;
}

.css-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.css-option {
  display: flex;
  gap: 8px;
  align-items: center;
}

.css-option .el-input {
  flex: 1;
}

.strategies-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.selector-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.selector-score {
  font-size: 12px;
  color: #909399;
  font-weight: bold;
}

.selector-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.selector-reason {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
  background: #f0f2f5;
  padding: 6px 8px;
  border-radius: 4px;
  border-left: 3px solid #409eff;
}

.recommendation-description {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 13px;
  color: #0066cc;
}

.strategy-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  background: #fafafa;
}

.strategy-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.strategy-description {
  font-size: 13px;
  color: #606266;
}

.strategy-selectors {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selector-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-row label {
  min-width: 50px;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.selector-row .el-input {
  flex: 1;
}

.mode-description {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
  font-style: italic;
  line-height: 1.4;
}
</style>