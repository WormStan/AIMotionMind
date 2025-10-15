<template>
  <div class="history-container">
    <el-card class="stats-card">
      <template #header>
        <div class="card-header">
          <span>📊 我的统计</span>
          <el-button type="primary" size="small" @click="refreshData">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20" v-if="stats">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_uploads }}</div>
            <div class="stat-label">上传视频</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_analyses }}</div>
            <div class="stat-label">分析报告</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ stats.storage_used }}</div>
            <div class="stat-label">存储空间</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ formatDate(stats.last_use) }}</div>
            <div class="stat-label">最后使用</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>📝 分析历史</span>
          <div class="header-actions">
            <el-tag>共 {{ history.analyses?.length || 0 }} 条记录</el-tag>
            <el-button type="primary" size="small" @click="$router.push('/')">
              <el-icon><Plus /></el-icon> 新建分析
            </el-button>
          </div>
        </div>
      </template>

      <el-empty v-if="!history.analyses || history.analyses.length === 0" description="暂无分析记录">
        <el-button type="primary" @click="$router.push('/')">
          开始第一次分析
        </el-button>
      </el-empty>

      <el-timeline v-else>
        <el-timeline-item
          v-for="analysis in history.analyses"
          :key="analysis.analysis_id"
          :timestamp="formatDateTime(analysis.analysis_time)"
          placement="top"
        >
          <el-card>
            <div class="analysis-item">
              <div class="analysis-info">
                <h4>
                  {{ analysis.metadata?.analysis_name || analysis.analysis_id }}
                  <el-tag v-if="analysis.metadata?.analysis_name" size="small" type="info">
                    {{ analysis.analysis_id }}
                  </el-tag>
                </h4>
                <p class="analysis-meta">
                  <el-tag type="success" size="small">{{ analysis.sport_type }}</el-tag>
                  <span class="video-name">{{ analysis.video_file || analysis.metadata?.video_file || '未知视频' }}</span>
                </p>
                <p class="analysis-summary" v-if="analysis.metadata">
                  <el-icon><Clock /></el-icon>
                  {{ formatDateTime(analysis.analysis_time) }}
                </p>
              </div>
              <div class="analysis-actions">
                <!-- 查看详细分析结果（跳转到Result页面） -->
                <el-button
                  type="primary"
                  size="small"
                  @click="viewAnalysisDetail(analysis)"
                >
                  <el-icon><View /></el-icon> 查看详情
                </el-button>
                
                <!-- 删除分析记录 -->
                <el-button
                  type="danger"
                  size="small"
                  plain
                  @click="deleteAnalysis(analysis)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 设备信息（开发调试用） -->
    <el-card class="device-card" v-if="showDebug">
      <template #header>
        <span>🔧 设备信息（调试）</span>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="设备ID">
          {{ history.device_id }}
          <el-button size="small" @click="copyDeviceId">复制</el-button>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserHistory, getUserStats } from '@/api/auth'
import { getDeviceId } from '@/utils/device'

const router = useRouter()
const history = ref({})
const stats = ref(null)
const showDebug = ref(import.meta.env.DEV) // 只在开发环境显示

// 加载数据
const loadData = async () => {
  try {
    // 获取历史记录
    const historyResult = await getUserHistory()
    if (historyResult && historyResult.data) {
      history.value = historyResult.data
    }

    // 获取统计信息
    const statsResult = await getUserStats()
    if (statsResult && statsResult.data) {
      stats.value = statsResult.data
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载历史记录失败')
  }
}

// 刷新数据
const refreshData = () => {
  ElMessage.info('正在刷新...')
  loadData()
}

// 查看分析详情（跳转到Result页面）
const viewAnalysisDetail = (analysis) => {
  router.push({
    name: 'Result',
    params: {
      analysisId: analysis.analysis_id
    },
    query: {
      sport_type: analysis.sport_type || 'basketball'
    }
  })
}

// 查看HTML报告（新窗口打开）
const viewReport = (analysis) => {
  // 构建报告URL
  const deviceId = getDeviceId()
  const reportUrl = `/api/files/report/${deviceId}/basketball/${analysis.analysis_id}/reports/basketball_analysis_report.html?device_id=${deviceId}`
  window.open(reportUrl, '_blank')
}

// 查看对比报告（新窗口打开）
const viewComparison = (analysis) => {
  const deviceId = getDeviceId()
  const comparisonUrl = `/api/files/report/${deviceId}/basketball/${analysis.analysis_id}/reports/keyframe_comparison_report.html?device_id=${deviceId}`
  window.open(comparisonUrl, '_blank')
}

// 删除分析记录
const deleteAnalysis = async (analysis) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分析记录 "${analysis.analysis_id}" 吗？此操作不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 实现删除API
    ElMessage.info('删除功能开发中...')
    // 删除成功后刷新列表
    // await deleteAnalysisRecord(analysis.analysis_id)
    // await loadData()
    // ElMessage.success('删除成功')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 复制设备ID
const copyDeviceId = () => {
  const deviceId = getDeviceId()
  navigator.clipboard.writeText(deviceId)
  ElMessage.success('设备ID已复制')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-card,
.history-card,
.device-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.analysis-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.analysis-info {
  flex: 1;
}

.analysis-info h4 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 16px;
}

.analysis-meta {
  margin: 0 0 8px 0;
  color: #909399;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.analysis-summary {
  margin: 0;
  color: #909399;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.video-name {
  color: #606266;
  font-weight: 500;
}

.analysis-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.analysis-actions .el-button {
  margin: 0;
}

/* 响应式设计 */

@media (max-width: 768px) {
  .analysis-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .analysis-actions {
    margin-top: 10px;
    width: 100%;
  }

  .analysis-actions .el-button {
    flex: 1;
  }
}
</style>
