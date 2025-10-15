<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 头部导航 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <el-icon class="logo-icon"><Basketball /></el-icon>
            <span class="logo-text">AIMotionMind</span>
          </div>
          <router-link to="/" class="nav-link">首页</router-link>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>

      <!-- 页脚 -->
      <el-footer class="app-footer">
        <p>© 2025 AIMotionMind - 篮球投篮AI分析系统</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  color: white;
  font-size: 20px;
  font-weight: bold;
}

.logo-icon {
  font-size: 28px;
  margin-right: 10px;
}

.nav-link {
  color: white;
  font-size: 18px;
  font-weight: 500;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.app-main {
  background: #f5f7fa;
  padding: 20px;
  min-height: calc(100vh - 120px);
}

.app-footer {
  background: #fff;
  text-align: center;
  color: #909399;
  line-height: 60px;
  box-shadow: 0 -2px 12px 0 rgba(0, 0, 0, 0.05);
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    padding: 10px;
  }

  .logo {
    margin-bottom: 10px;
  }

  .header-menu {
    width: 100%;
  }

  .app-main {
    padding: 10px;
  }

  .logo-text {
    font-size: 16px;
  }
}
</style>
