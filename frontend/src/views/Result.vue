<template>
  <div class="result-page" v-loading="loading">
    <div v-if="result" class="container">
      <!-- 头部 -->
      <div class="header">
        <h1>
          🏀 {{ result.title || '篮球投篮动作分析报告' }}
          <el-tag v-if="result.is_demo" type="warning" effect="dark" style="margin-left: 15px;">
            <el-icon><Star /></el-icon> 明星示例
          </el-tag>
        </h1>
        <p v-if="result.description" class="description">{{ result.description }}</p>
        <div class="analysis-info">
          <span v-if="!result.is_demo">分析ID: {{ analysisId }}</span>
          <span v-if="result.timestamp">生成时间: {{ formatTimestamp(result.timestamp) }}</span>
        </div>
      </div>

      <!-- 主要分析区域：左侧视频，右侧实时图表 -->
      <div class="main-analysis" v-if="result.analysis_results">
        <!-- 左侧：视频播放器 -->
        <div class="video-section">
          <h2>📹 投篮视频</h2>
          <video 
            ref="videoPlayer" 
            controls 
            @timeupdate="onVideoTimeUpdate"
            @loadedmetadata="onVideoLoaded"
          >
            <source :src="getVideoUrl()" type="video/mp4">
            您的浏览器不支持视频播放。
          </video>
          
          <div class="video-info">
            <p><strong>帧率:</strong> {{ result.video_info?.fps || 30 }} FPS</p>
            <p><strong>总帧数:</strong> {{ result.video_info?.frame_count || 0 }} 帧</p>
            <p><strong>时长:</strong> {{ result.video_info?.duration?.toFixed(2) || 0 }} 秒</p>
          </div>
        </div>

        <!-- 右侧：实时同步图表 -->
        <div class="realtime-charts">
          <h2>📊 实时数据曲线</h2>
          <p class="chart-hint">
            <small>📍 红线表示当前播放位置 | 虚线表示关键帧</small>
          </p>
          
          <div class="chart-container">
            <canvas ref="realtimeChart"></canvas>
          </div>
          
          <!-- 当前帧数据显示 -->
          <div class="current-data-display">
            <h4>📌 当前帧数据</h4>
            <div v-if="currentFrameData" class="current-data-grid">
              <div class="data-item">
                <span class="label">当前帧:</span>
                <span class="value">{{ currentFrame }}</span>
              </div>
              <div class="data-item">
                <span class="label">时间:</span>
                <span class="value">{{ currentTime.toFixed(2) }} 秒</span>
              </div>
              <div v-if="currentFrameData.angles" class="angles-grid">
                <div v-for="(value, key) in currentFrameData.angles" :key="key" class="data-item">
                  <span class="label">{{ getAngleLabel(key) }}:</span>
                  <span class="value">{{ value?.toFixed(2) }}°</span>
                </div>
              </div>
            </div>
            <p v-else class="waiting-text">等待视频播放...</p>
          </div>
        </div>
      </div>

      <!-- 详细数据图表区域 -->
      <div class="detailed-charts" v-if="result.analysis_results">
        <h2>📈 详细运动数据分析</h2>
        
        <!-- 角度变化分组 -->
        <div class="chart-group">
          <h3 class="group-title">📐 角度变化</h3>
          <div class="charts-grid">
            <!-- 膝关节角度 -->
            <div class="chart-item">
              <h3>膝关节角度</h3>
              <canvas ref="kneeChart"></canvas>
            </div>

            <!-- 肘关节角度 -->
            <div class="chart-item">
              <h3>肘关节角度</h3>
              <canvas ref="elbowChart"></canvas>
            </div>

            <!-- 肩关节角度 -->
            <div class="chart-item">
              <h3>肩关节角度</h3>
              <canvas ref="shoulderChart"></canvas>
            </div>

            <!-- 躯干倾斜 -->
            <div class="chart-item">
              <h3>躯干倾斜角度</h3>
              <canvas ref="trunkChart"></canvas>
            </div>
          </div>
        </div>

        <!-- 速度变化分组 -->
        <div class="chart-group">
          <h3 class="group-title">💨 速度变化</h3>
          <div class="charts-grid">
            <!-- 手腕速度 -->
            <div class="chart-item">
              <h3>手腕速度</h3>
              <canvas ref="wristVelocityChart"></canvas>
            </div>

            <!-- 肘部速度 -->
            <div class="chart-item">
              <h3>肘部速度</h3>
              <canvas ref="elbowVelocityChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- 高级分析指标 -->
      <div class="advanced-analysis" v-if="result.analysis_results">
        <h2>🔬 高级运动学分析</h2>
        
        <el-row :gutter="20">
          <!-- 动作节奏分析 -->
          <el-col :xs="24" :sm="12" :lg="8">
            <el-card class="analysis-card">
              <template #header>
                <h3>⏱️ 动作节奏分析</h3>
              </template>
              <div v-if="rhythmAnalysis">
                <el-alert 
                  type="info" 
                  :closable="false"
                  style="margin-bottom: 15px"
                >
                  <template #title>
                    <small>📍 分析范围: 从<strong>球最低点</strong>开始</small>
                  </template>
                </el-alert>
                
                <div class="metric-item">
                  <span class="metric-label">投篮时长</span>
                  <span class="metric-value">{{ (rhythmAnalysis.shooting_duration || rhythmAnalysis.total_duration || 0).toFixed(2) }} 秒</span>
                  <div class="metric-hint">(从球最低点到结束)</div>
                </div>
                
                <div class="metric-item">
                  <span class="metric-label">节奏一致性</span>
                  <span class="metric-value" :class="getConsistencyClass(rhythmAnalysis.rhythm_consistency)">
                    {{ (rhythmAnalysis.rhythm_consistency || 0).toFixed(3) }}
                  </span>
                  <div class="metric-hint">(越小越好)</div>
                </div>

                <div v-if="rhythmAnalysis.key_phases" style="margin-top: 15px">
                  <h4>关键阶段时长</h4>
                  <div v-for="(duration, phase) in rhythmAnalysis.key_phases" :key="phase" class="metric-item">
                    <span class="metric-label">{{ getPhaseLabel(phase) }}</span>
                    <span class="metric-value">{{ duration.toFixed(2) }} 秒</span>
                  </div>
                </div>
              </div>
              <div v-else class="no-data">暂无数据</div>
            </el-card>
          </el-col>

          <!-- 发力启动顺序 -->
          <el-col :xs="24" :sm="12" :lg="8">
            <el-card class="analysis-card">
              <template #header>
                <h3>⚡ 发力启动顺序分析</h3>
              </template>
              <div v-if="forceSequence">
                <el-alert 
                  type="success" 
                  :closable="false"
                  style="margin-bottom: 15px"
                >
                  <template #title>
                    <small>📍 分析范围: 从<strong>球最低点</strong>开始</small>
                  </template>
                </el-alert>

                <div v-if="forceSequence.pattern_analysis" class="force-pattern">
                  <h4>发力启动顺序</h4>
                  <div class="sequence-flow">
                    <template v-for="(part, index) in forceSequence.pattern_analysis.initiation_order" :key="index">
                      <el-tag :type="getPartTagType(part)" size="large">
                        {{ getPartLabel(part) }}
                      </el-tag>
                      <span v-if="index < forceSequence.pattern_analysis.initiation_order.length - 1" class="arrow">→</span>
                    </template>
                  </div>

                  <div v-if="forceSequence.pattern_analysis.key_parts" style="margin-top: 15px">
                    <div class="metric-item">
                      <span class="metric-label">下肢启动</span>
                      <span class="metric-value">第 {{ forceSequence.pattern_analysis.key_parts.lower }} 帧</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-label">髋部启动</span>
                      <span class="metric-value">第 {{ forceSequence.pattern_analysis.key_parts.hip }} 帧</span>
                    </div>
                    <div class="metric-item">
                      <span class="metric-label">上肢启动</span>
                      <span class="metric-value">第 {{ forceSequence.pattern_analysis.key_parts.upper }} 帧</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="no-data">暂无数据</div>
            </el-card>
          </el-col>

          <!-- 力量传递协调性 -->
          <el-col :xs="24" :sm="12" :lg="8">
            <el-card class="analysis-card">
              <template #header>
                <h3>💪 力量传递协调性</h3>
              </template>
              <div v-if="energyTransfer">
                <el-alert 
                  type="warning" 
                  :closable="false"
                  style="margin-bottom: 15px"
                >
                  <template #title>
                    <small>📍 分析范围: 从<strong>球最低点</strong>到出手</small>
                  </template>
                </el-alert>

                <h4>速度分析</h4>
                <div class="metric-item">
                  <span class="metric-label">下肢峰值速度</span>
                  <span class="metric-value">{{ (energyTransfer.lower_body_peak_velocity || 0).toFixed(2) }}</span>
                  <div class="metric-hint">第{{ energyTransfer.lower_peak_frame || 0 }}帧</div>
                </div>
                <div class="metric-item">
                  <span class="metric-label">上肢峰值速度</span>
                  <span class="metric-value">{{ (energyTransfer.upper_body_peak_velocity || 0).toFixed(2) }}</span>
                  <div class="metric-hint">第{{ energyTransfer.upper_peak_frame || 0 }}帧</div>
                </div>
                <div class="metric-item">
                  <span class="metric-label">速度放大比</span>
                  <span class="metric-value">{{ (energyTransfer.velocity_ratio || 0).toFixed(2) }}x</span>
                </div>

                <h4 style="margin-top: 15px">时序分析</h4>
                <div class="metric-item">
                  <span class="metric-label">峰值时间差</span>
                  <span class="metric-value">{{ energyTransfer.timing_difference || 0 }} 帧</span>
                  <div class="metric-hint">{{ energyTransfer.transfer_timing || '' }}</div>
                </div>
              </div>
              <div v-else class="no-data">暂无数据</div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 关键帧分析 -->
      <div class="keyframes-section" v-if="sortedKeyframes.length > 0">
        <h2>🎯 关键帧分析</h2>
        <el-row :gutter="20">
          <el-col
            v-for="([kfName, kfData], index) in sortedKeyframes"
            :key="kfName"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <el-card class="keyframe-card" shadow="hover">
              <img
                :src="getKeyframeUrl(kfName)"
                :alt="kfData.description"
                class="keyframe-image"
              />
              <div class="keyframe-info">
                <h3>{{ kfData.description }}</h3>
                <p><strong>时间:</strong> {{ kfData.frame_data.timestamp?.toFixed(2) }} 秒</p>
                <p><strong>帧号:</strong> {{ kfData.index }}</p>
                
                <div v-if="kfData.frame_data.angles" class="keyframe-data">
                  <h4>关节角度数据</h4>
                  <div v-for="(angleValue, angleName) in kfData.frame_data.angles" :key="angleName" class="data-item">
                    <span class="data-label">{{ getAngleLabel(angleName) }}</span>
                    <span class="data-value">{{ angleValue?.toFixed(2) }}°</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 页脚 -->
      <div class="footer">
        <p>© 2025 篮球投篮分析系统 | 基于 MediaPipe & OpenCV</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, onUnmounted, markRaw } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star } from '@element-plus/icons-vue'
import { getAnalysisResult, getFileUrl } from '@/api/analysis'
import { Chart, registerables } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'

// 注册 Chart.js 组件
Chart.register(...registerables, annotationPlugin)

const route = useRoute()
const analysisId = ref(route.params.analysisId)
const loading = ref(true)
const result = ref(null)

// 视频相关
const videoPlayer = ref(null)
const currentFrame = ref(0)
const currentTime = ref(0)
const currentFrameData = ref(null)

// 图表相关
const realtimeChart = ref(null)
const kneeChart = ref(null)
const elbowChart = ref(null)
const shoulderChart = ref(null)
const wristVelocityChart = ref(null)
const elbowVelocityChart = ref(null)
const trunkChart = ref(null)

const charts = ref({})

// 计算属性
const rhythmAnalysis = computed(() => result.value?.analysis_results?.rhythm_analysis)
const forceSequence = computed(() => result.value?.analysis_results?.force_sequence)
const energyTransfer = computed(() => result.value?.analysis_results?.energy_transfer)

// 关键帧优先级定义（数字越小优先级越高）
const keyframePriority = {
  'ball_lowest': 1,              // 球的最低点
  'lift_start': 2,               // 开始持续抬球
  'ball_rising_mid': 3,          // 球上升中点
  'ball_at_chest': 4,            // 球到胸部高度
  'ball_at_shoulder': 5,         // 球到肩部高度
  'squat_deepest': 6,            // 重心最低点（下蹲最深）
  'leg_power_start': 7,          // 腿部开始发力（蹬伸）
  'power_transfer': 8,           // 力量传递
  'elbow_max_bend': 9,           // 肘关节最大弯曲
  'wrist_snap': 10,              // 手腕下压（snap）
  'release_prepare': 11,         // 出手准备
  'elbow_extension_max': 12,     // 肘关节伸展最快
  'release': 13,                 // 出手瞬间
  'follow_through': 14,          // 随球动作完成（手腕最高点）
  'arm_full_extension': 15       // 手臂完全伸展
}

// 按时间顺序排序的关键帧，时间相同时按优先级排序
const sortedKeyframes = computed(() => {
  if (!result.value?.keyframes) return []
  
  // 将对象转换为数组并排序
  return Object.entries(result.value.keyframes)
    .sort((a, b) => {
      const indexA = a[1]?.index || 0
      const indexB = b[1]?.index || 0
      
      // 首先按帧索引（时间）排序
      if (indexA !== indexB) {
        return indexA - indexB
      }
      
      // 如果帧索引相同，按优先级排序
      const priorityA = keyframePriority[a[0]] || 999
      const priorityB = keyframePriority[b[0]] || 999
      return priorityA - priorityB
    })
})

const loadResult = async () => {
  try {
    loading.value = true
    const res = await getAnalysisResult(analysisId.value)
    result.value = res.data
    console.log('Analysis result:', res.data)
    
    // 等待 DOM 更新后初始化图表
    await nextTick()
    initCharts()
  } catch (error) {
    console.error('Load error:', error)
    ElMessage.error('加载分析结果失败')
  } finally {
    loading.value = false
  }
}

const getVideoUrl = () => {
  // 视频文件在 uploads 目录中
  const videoPath = result.value?.video_info?.path
  if (videoPath) {
    // 如果是curry_demo，直接使用public路径
    if (analysisId.value === 'curry_demo' && videoPath.startsWith('/star_report/')) {
      return videoPath
    }
    
    // 提取文件名（去除路径）
    const filename = videoPath.split(/[/\\]/).pop()
    return getFileUrl('upload', filename)
  }
  return ''
}

const onVideoLoaded = () => {
  console.log('Video loaded')
  
  // 检测视频是否为竖屏，并调整样式
  if (videoPlayer.value) {
    const videoWidth = videoPlayer.value.videoWidth
    const videoHeight = videoPlayer.value.videoHeight
    const isPortrait = videoHeight > videoWidth
    
    if (isPortrait) {
      console.log(`检测到竖屏视频: ${videoWidth}x${videoHeight}`)
      // 对竖屏视频应用更严格的高度限制
      videoPlayer.value.style.maxHeight = '60vh'
      videoPlayer.value.style.width = 'auto'
      videoPlayer.value.style.maxWidth = '100%'
    } else {
      console.log(`检测到横屏视频: ${videoWidth}x${videoHeight}`)
      // 横屏视频保持原有样式
      videoPlayer.value.style.maxHeight = '70vh'
      videoPlayer.value.style.width = '100%'
    }
  }
}

const onVideoTimeUpdate = () => {
  if (!videoPlayer.value || !result.value?.analysis_results) return
  
  const fps = result.value.video_info?.fps || 30
  currentTime.value = videoPlayer.value.currentTime
  currentFrame.value = Math.floor(currentTime.value * fps)
  
  // 更新当前帧数据 - 找到最接近的帧
  const frames = result.value.analysis_results.frames || []
  
  if (frames.length === 0) return
  
  // 先尝试精确匹配
  let foundFrame = frames.find(f => f.frame_number === currentFrame.value)
  
  // 如果没有精确匹配，找最接近的帧
  if (!foundFrame) {
    foundFrame = frames.reduce((closest, frame) => {
      const currentDiff = Math.abs(frame.frame_number - currentFrame.value)
      const closestDiff = Math.abs(closest.frame_number - currentFrame.value)
      return currentDiff < closestDiff ? frame : closest
    }, frames[0])
  }
  
  // 更新当前帧数据
  if (foundFrame) {
    currentFrameData.value = foundFrame
    // 调试信息（可选，帮助诊断问题）
    if (foundFrame.frame_number !== currentFrame.value) {
      console.log(`使用最接近的帧: ${foundFrame.frame_number} (目标: ${currentFrame.value})`)
    }
  }
  
  // 更新实时图表的当前位置标记
  updateRealtimeChartMarker()
}

const updateRealtimeChartMarker = () => {
  const chart = charts.value.realtime
  if (!chart || !chart.options || !chart.options.plugins || !chart.options.plugins.annotation) {
    return
  }
  
  // 更新当前时间线的位置
  try {
    if (chart.options.plugins.annotation.annotations && chart.options.plugins.annotation.annotations.currentTimeLine) {
      chart.options.plugins.annotation.annotations.currentTimeLine.xMin = currentTime.value
      chart.options.plugins.annotation.annotations.currentTimeLine.xMax = currentTime.value
      chart.update('none') // 使用 'none' 模式避免动画，提高性能
    }
  } catch (error) {
    console.error('Error updating chart marker:', error)
  }
}

const initCharts = () => {
  if (!result.value?.analysis_results) {
    console.warn('No analysis results available')
    return
  }
  
  const analysisResults = result.value.analysis_results
  const frames = analysisResults.frames || []
  
  if (frames.length === 0) {
    console.warn('No frames data available')
    return
  }
  
  console.log('Initializing charts with', frames.length, 'frames')
  
  // 准备数据
  const timestamps = frames.map(f => f.timestamp)
  const fps = result.value.video_info?.fps || 30
  
  // 创建实时图表
  createRealtimeChart(timestamps, frames, fps)
  
  // 创建详细图表
  createAngleChart('knee', kneeChart.value, timestamps, frames, 'knee_angle', '膝关节角度')
  createAngleChart('elbow', elbowChart.value, timestamps, frames, 'elbow_angle', '肘关节角度')
  createAngleChart('shoulder', shoulderChart.value, timestamps, frames, 'shoulder_angle', '肩关节角度')
  createAngleChart('trunk', trunkChart.value, timestamps, frames, 'trunk_lean', '躯干倾斜')
  
  createVelocityChart('wristVelocity', wristVelocityChart.value, timestamps, frames, 'right_wrist', '手腕速度')
  createVelocityChart('elbowVelocity', elbowVelocityChart.value, timestamps, frames, 'right_elbow', '肘部速度')
  
  console.log('Charts initialized successfully')
}

const createRealtimeChart = (timestamps, frames, fps) => {
  if (!realtimeChart.value) {
    console.warn('Realtime chart canvas not found')
    return
  }
  
  const ctx = realtimeChart.value.getContext('2d')
  
  // 准备多条数据线 - 使用 {x, y} 格式
  const datasets = [
    {
      label: '膝关节角度',
      data: frames.map(f => ({ x: f.timestamp, y: f.angles?.knee_angle })),
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.1)',
      yAxisID: 'y',
    },
    {
      label: '肘关节角度',
      data: frames.map(f => ({ x: f.timestamp, y: f.angles?.elbow_angle })),
      borderColor: 'rgb(255, 99, 132)',
      backgroundColor: 'rgba(255, 99, 132, 0.1)',
      yAxisID: 'y',
    },
  ]
  
  // 准备关键帧标记 - 只显示三个关键的关键帧
  const keyframeAnnotations = {}
  if (result.value.keyframes) {
    // 定义需要显示的关键帧（使用实际的后端关键帧名称）
    const importantKeyframes = ['ball_lowest', 'elbow_max_bend', 'follow_through']
    const keyframeLabels = {
      'ball_lowest': '球最低点',
      'elbow_max_bend': '肘关节最大弯曲',
      'follow_through': '随球动作完成'
    }
    
    Object.entries(result.value.keyframes).forEach(([name, data]) => {
      // 只处理重要的关键帧
      if (importantKeyframes.includes(name)) {
        const timestamp = data.frame_data?.timestamp || (data.index / fps)
        keyframeAnnotations[`keyframe_${name}`] = {
          type: 'line',
          xMin: timestamp,
          xMax: timestamp,
          borderColor: 'rgba(255, 159, 64, 0.8)',
          borderWidth: 2,
          borderDash: [5, 5],
          label: {
            display: true,
            content: keyframeLabels[name] || data.description,
            position: 'top',
            backgroundColor: 'rgba(255, 159, 64, 0.9)',
            color: 'white',
            font: {
              size: 11,
              weight: 'bold'
            }
          }
        }
      }
    })
  }
  
  // 使用 markRaw 避免 Vue 响应式包装导致的问题
  charts.value.realtime = markRaw(new Chart(ctx, {
    type: 'line',
    data: {
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top',
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null) {
                label += context.parsed.y.toFixed(2);
              }
              return label;
            },
            title: function(context) {
              return '时间: ' + context[0].parsed.x.toFixed(2) + '秒';
            }
          }
        },
        annotation: {
          annotations: {
            ...keyframeAnnotations,
            currentTimeLine: {
              type: 'line',
              xMin: 0,
              xMax: 0,
              borderColor: 'rgb(255, 0, 0)',
              borderWidth: 2,
              label: {
                display: true,
                content: '当前位置',
                position: 'start'
              }
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: '时间 (秒)'
          },
          ticks: {
            callback: function(value, index, ticks) {
              return value.toFixed(2);
            }
          }
        },
        y: {
          title: {
            display: true,
            text: '角度 (度)'
          },
          position: 'left',
          ticks: {
            callback: function(value, index, ticks) {
              return value.toFixed(2);
            }
          }
        }
      }
    }
  }))
  
  console.log('Realtime chart created:', charts.value.realtime ? 'success' : 'failed')
}

const createAngleChart = (id, canvas, timestamps, frames, angleKey, label) => {
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const data = frames.map(f => ({ x: f.timestamp, y: f.angles?.[angleKey] }))
  
  charts.value[id] = markRaw(new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: label,
        data: data,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null) {
                label += context.parsed.y.toFixed(2) + '°';
              }
              return label;
            },
            title: function(context) {
              return '时间: ' + context[0].parsed.x.toFixed(2) + '秒';
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: '时间 (秒)'
          },
          ticks: {
            callback: function(value, index, ticks) {
              return value.toFixed(2);
            }
          }
        },
        y: {
          title: {
            display: true,
            text: '角度 (度)'
          },
          ticks: {
            callback: function(value, index, ticks) {
              return value.toFixed(2);
            }
          }
        }
      }
    }
  }))
}

const createVelocityChart = (id, canvas, timestamps, frames, jointKey, label) => {
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const data = frames.map(f => ({ x: f.timestamp, y: f.velocities?.[jointKey] }))
  
  charts.value[id] = markRaw(new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [{
        label: label,
        data: data,
        borderColor: 'rgb(153, 102, 255)',
        backgroundColor: 'rgba(153, 102, 255, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null) {
                label += context.parsed.y.toFixed(2);
              }
              return label;
            },
            title: function(context) {
              return '时间: ' + context[0].parsed.x.toFixed(2) + '秒';
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: '时间 (秒)'
          },
          ticks: {
            callback: function(value, index, ticks) {
              return value.toFixed(2);
            }
          }
        },
        y: {
          title: {
            display: true,
            text: '速度 (像素/帧)'
          },
          ticks: {
            callback: function(value, index, ticks) {
              return value.toFixed(2);
            }
          }
        }
      }
    }
  }))
}

const getKeyframeUrl = (kfName) => {
  const path = `basketball/${analysisId.value}/keyframes/keyframe_${kfName}.jpg`
  return getFileUrl('keyframe', path)
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return ''
  // 格式化时间戳，假设格式为 20251015_131358
  const year = timestamp.substring(0, 4)
  const month = timestamp.substring(4, 6)
  const day = timestamp.substring(6, 8)
  const hour = timestamp.substring(9, 11)
  const minute = timestamp.substring(11, 13)
  const second = timestamp.substring(13, 15)
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const getConsistencyClass = (value) => {
  if (!value) return ''
  if (value < 0.2) return 'good'
  if (value < 0.5) return 'medium'
  return 'poor'
}

const getPhaseLabel = (phase) => {
  const labels = {
    'preparation': '预备阶段',
    'power_phase': '发力阶段',
    'follow_through': '跟随阶段'
  }
  return labels[phase] || phase
}

const getPartLabel = (part) => {
  const labels = {
    'lower': '下肢',
    'hip': '髋部',
    'upper': '上肢'
  }
  return labels[part] || part
}

const getPartTagType = (part) => {
  const types = {
    'lower': 'success',
    'hip': 'warning',
    'upper': 'primary'
  }
  return types[part] || ''
}

const getAngleLabel = (angleName) => {
  const labels = {
    'knee_angle': '膝关节角度',
    'hip_angle': '髋关节角度',
    'elbow_angle': '肘关节角度',
    'shoulder_angle': '肩关节角度',
    'wrist_angle': '手腕角度',
    'trunk_lean': '躯干倾斜'
  }
  return labels[angleName] || angleName
}

onMounted(() => {
  loadResult()
})

onUnmounted(() => {
  // 清理所有图表
  Object.values(charts.value).forEach(chart => {
    if (chart) chart.destroy()
  })
})
</script>

<style scoped>
.result-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
}

/* 头部样式 */
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5em;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.header .description {
  margin: 10px 0 15px 0;
  font-size: 1.1em;
  opacity: 0.9;
}

.analysis-info {
  display: flex;
  justify-content: center;
  gap: 30px;
  font-size: 0.9em;
  opacity: 0.8;
}

/* 主分析区域：视频和实时图表 */
.main-analysis {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.video-section,
.realtime-charts {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.video-section {
  display: flex;
  flex-direction: column;
  align-items: center; /* 竖屏视频居中显示 */
}

.video-section h2,
.realtime-charts h2 {
  align-self: flex-start; /* 标题左对齐 */
  width: 100%;
  margin: 0 0 15px 0;
  font-size: 1.5em;
  color: #333;
}

.video-section video {
  width: 100%;
  max-height: 70vh; /* 限制最大高度为视口高度的70% */
  border-radius: 8px;
  background: #000;
  object-fit: contain; /* 保持宽高比，完整显示视频内容 */
  display: block;
  margin: 0 auto; /* 居中显示 */
}

.video-info {
  width: 100%; /* 确保信息区域占满宽度 */
  margin-top: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.video-info p {
  margin: 5px 0;
  color: #666;
}

/* 当前帧数据显示（右侧） */
.current-data-display {
  margin: 20px 0 0 0;
  padding: 15px 20px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.current-data-display h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 1.1em;
  font-weight: 600;
}

.current-data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.angles-grid {
  grid-column: 1 / -1; /* 占满整行 */
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin-top: 5px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.data-item .label {
  font-size: 0.9em;
  color: #666;
  font-weight: 500;
}

.data-item .value {
  font-size: 1em;
  font-weight: 700;
  color: #409eff;
}

.waiting-text {
  margin: 0;
  text-align: center;
  color: #999;
  font-style: italic;
}

.chart-hint {
  color: #666;
  margin-bottom: 10px;
}

.chart-container {
  position: relative;
  height: 400px;
}

/* 详细图表区域 */
.detailed-charts {
  margin-bottom: 30px;
}

.detailed-charts > h2 {
  font-size: 1.8em;
  color: #333;
  margin-bottom: 20px;
  padding-left: 15px;
  border-left: 4px solid #667eea;
}

.chart-group {
  margin-bottom: 30px;
}

.group-title {
  font-size: 1.3em;
  color: #555;
  margin-bottom: 15px;
  padding-left: 12px;
  border-left: 3px solid #409eff;
  font-weight: 600;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 20px;
}

.chart-item {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-item h3 {
  margin: 0 0 15px 0;
  font-size: 1.1em;
  color: #333;
  text-align: center;
}

.chart-item canvas {
  height: 250px !important;
}

/* 视频信息卡片（已移除）*/

/* 高级分析区域 */
.advanced-analysis {
  margin-bottom: 30px;
}

.advanced-analysis > h2 {
  font-size: 1.8em;
  color: #333;
  margin-bottom: 20px;
  padding-left: 15px;
  border-left: 4px solid #667eea;
}

.analysis-card {
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.analysis-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.analysis-card h3 {
  margin: 0;
  font-size: 1.2em;
  color: #333;
}

.analysis-card h4 {
  font-size: 1em;
  color: #555;
  margin: 15px 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 2px solid #e0e0e0;
}

/* 指标项样式 */
.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.metric-item:last-child {
  border-bottom: none;
}

.metric-label {
  color: #666;
  font-size: 0.95em;
}

.metric-value {
  font-weight: 600;
  font-size: 1.1em;
  color: #333;
}

.metric-value.good {
  color: #67c23a;
}

.metric-value.medium {
  color: #e6a23c;
}

.metric-value.poor {
  color: #f56c6c;
}

.metric-hint {
  font-size: 0.85em;
  color: #999;
  margin-top: 2px;
}

/* 发力启动顺序样式 */
.force-pattern {
  margin-top: 10px;
}

.sequence-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px;
  background: #f9fbe7;
  border-radius: 8px;
  border-left: 4px solid #827717;
  margin: 10px 0;
}

.arrow {
  color: #666;
  font-size: 20px;
  font-weight: bold;
}

.no-data {
  color: #999;
  text-align: center;
  padding: 20px;
  font-style: italic;
}

/* 关键帧区域 */
.keyframes-section {
  margin-bottom: 30px;
}

.keyframes-section > h2 {
  font-size: 1.8em;
  color: #333;
  margin-bottom: 20px;
  padding-left: 15px;
  border-left: 4px solid #667eea;
}

.keyframe-card {
  margin-bottom: 20px;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.keyframe-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.keyframe-image {
  width: 100%;
  height: auto;
  max-height: 400px;
  object-fit: contain;
  display: block;
  background-color: #f5f5f5;
}

.keyframe-info {
  padding: 15px;
}

.keyframe-info h3 {
  margin: 0 0 10px 0;
  font-size: 1.1em;
  color: #333;
}

.keyframe-info p {
  margin: 5px 0;
  color: #666;
  font-size: 0.9em;
}

.keyframe-data {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.keyframe-data h4 {
  margin: 0 0 10px 0;
  font-size: 0.95em;
  color: #555;
}

.data-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.data-item:last-child {
  border-bottom: none;
}

.data-label {
  color: #666;
  font-size: 0.9em;
}

.data-value {
  font-weight: 600;
  color: #667eea;
  font-size: 1em;
}

/* 页脚 */
.footer {
  text-align: center;
  padding: 30px 20px;
  color: #999;
  font-size: 0.9em;
  border-top: 1px solid #e0e0e0;
  margin-top: 40px;
}

.footer p {
  margin: 5px 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .main-analysis {
    grid-template-columns: 1fr;
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header h1 {
    font-size: 1.8em;
  }
  
  .analysis-info {
    flex-direction: column;
    gap: 10px;
  }
  
  .keyframe-image {
    max-height: 300px;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .chart-item canvas {
    height: 200px !important;
  }
}
</style>
