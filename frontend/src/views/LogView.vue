<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { logService } from '@/services/api';
import { ElMessage } from 'element-plus';

const logs = ref('');
const isLoading = ref(false);

const fetchLogs = async () => {
  isLoading.value = true;
  try {
    const response = await logService.getLogs();
    logs.value = response.data;
  } catch (error) {
    ElMessage.error('获取日志失败。');
    logs.value = '无法加载日志文件。请检查后端服务是否正常，以及日志文件是否存在。';
    console.error(error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchLogs);
</script>

<template>
  <el-card class="log-card">
    <template #header>
      <div class="card-header">
        <span>系统日志 (logs/monitor.log)</span>
        <el-button type="primary" :loading="isLoading" @click="fetchLogs">刷新</el-button>
      </div>
    </template>
    <div class="log-container">
      <pre class="log-content">{{ logs }}</pre>
    </div>
  </el-card>
</template>

<style scoped>
.log-card {
  height: calc(100vh - 108px); /* Full height minus header and padding */
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  height: 100%;
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-container {
  height: 100%;
  overflow-y: scroll;
  background-color: #1e1e1e; /* Dark background */
  color: #d4d4d4; /* Light text */
  padding: 20px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 14px;
  line-height: 1.5;
}

.log-content {
  margin: 0;
  white-space: pre-wrap; /* Wrap long lines */
  word-break: break-all;
}
</style> 