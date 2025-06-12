<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, RouterView } from 'vue-router'

const route = useRoute()
const activeRoute = ref(route.path)

// Watch for route changes to update the active menu item
watch(() => route.path, (newPath) => {
  activeRoute.value = newPath
})

const handleSelect = (key: string) => {
  activeRoute.value = key
}
</script>

<template>
  <el-container class="main-layout">
    <el-header class="header">
      <div class="logo">
        <img alt="logo" src="@/assets/logo.svg" width="32" height="32" />
        <span class="title">网页内容监控系统</span>
      </div>
      <el-menu
        :default-active="activeRoute"
        class="navigation-menu"
        mode="horizontal"
        :router="true"
        @select="handleSelect"
      >
        <el-menu-item index="/">任务管理</el-menu-item>
        <el-menu-item index="/selector">元素选择器</el-menu-item>
        <el-menu-item index="/logs">日志查看</el-menu-item>
        <el-menu-item index="/settings">通知设置</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
/* Global styles */
body {
  margin: 0;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
}
</style>

<style scoped>
.main-layout {
  min-height: 100vh;
  background-color: #f0f2f5;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #ffffff;
  border-bottom: 1px solid #dcdfe6;
  padding: 0 40px;
  height: 60px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.main-content {
  /* Padding is now handled by individual views */
}

.navigation-menu {
  border-bottom: none; /* Remove the default border from the menu */
}
</style>
