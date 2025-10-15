<template>
  <div class="analysis-page">
    <el-card class="progress-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>视频分析中</span>
        </div>
      </template>

      <div class="progress-content">
        <el-icon class="loading-icon"><loading /></el-icon>
        
        <h2>{{ taskStatus.message }}</h2>
        
        <el-progress
          :percentage="taskStatus.progress"
          :status="getProgressStatus()"
          :stroke-width="24"
        />
        
        <p class="progress-detail">
          进度: {{ taskStatus.progress }}%
        </p>
        
        <p class="task-info">
          任务ID: {{ taskId }}
        </p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTaskStatus } from '@/api/analysis'

const route = useRoute()
const router = useRouter()
const taskId = ref(route.params.taskId)
const taskStatus = ref({
  status: 'pending',
  progress: 0,
  message: '准备开始分析...'
})

let pollingTimer = null

// 轮询查询任务状态
const pollTaskStatus = async () => {
  try {
    const res = await getTaskStatus(taskId.value)
    taskStatus.value = res.data

    // 如果任务完成，跳转到结果页
    if (res.data.status === 'completed') {
      clearPolling()
      ElMessage.success('分析完成！')
      router.push(`/result/${res.data.analysis_id}`)
    }

    // 如果任务失败，显示错误
    if (res.data.status === 'failed') {
      clearPolling()
      ElMessage.error(`分析失败: ${res.data.error || '未知错误'}`)
    }
  } catch (error) {
    console.error('查询任务状态失败:', error)
  }
}

const clearPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const getProgressStatus = () => {
  if (taskStatus.value.status === 'completed') return 'success'
  if (taskStatus.value.status === 'failed') return 'exception'
  return undefined
}

onMounted(() => {
  // 立即查询一次
  pollTaskStatus()
  
  // 每2秒轮询一次
  pollingTimer = setInterval(pollTaskStatus, 2000)
})

onUnmounted(() => {
  clearPolling()
})
</script>

<style scoped>
.analysis-page {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.progress-content {
  padding: 60px 40px;
  text-align: center;
}

.loading-icon {
  font-size: 80px;
  color: #409eff;
  animation: rotate 2s linear infinite;
  margin-bottom: 30px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-content h2 {
  margin: 0 0 30px 0;
  color: #303133;
}

.progress-detail {
  margin-top: 20px;
  font-size: 16px;
  color: #606266;
}

.task-info {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
