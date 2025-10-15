<template>
  <div class="upload-page">
    <el-card class="upload-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Upload /></el-icon>
          <span>上传投篮视频</span>
        </div>
      </template>

      <!-- 文件上传区 -->
      <div v-if="!uploading && !analyzing" class="upload-area">
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :before-upload="beforeUpload"
          :show-file-list="false"
          accept="video/*"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将视频文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 MP4、WEBM 格式，文件大小不超过 10MB
            </div>
          </template>
        </el-upload>

        <!-- 已选择的文件 -->
        <div v-if="selectedFile" class="file-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="文件名">
              {{ selectedFile.name }}
            </el-descriptions-item>
            <el-descriptions-item label="大小">
              {{ formatFileSize(selectedFile.size) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 分析选项 -->
        <div v-if="selectedFile" class="options-section">
          <h3>分析选项</h3>
          <el-form :model="options" label-width="120px">
            <el-form-item label="分析名称">
              <el-input
                v-model="options.analysis_name"
                placeholder="输入自定义名称（可选）"
                clearable
              >
                <template #append>
                  <el-button @click="generateName">
                    <el-icon><Refresh /></el-icon> 自动生成
                  </el-button>
                </template>
              </el-input>
              <div class="form-tip">
                为本次分析设置一个易于识别的名称，如"库里投篮训练-第1天"
              </div>
            </el-form-item>
            
            <el-form-item label="帧提取间隔">
              <el-input-number
                v-model="options.frame_interval"
                :min="1"
                :max="30"
                :step="1"
              />
              <span class="form-tip">
                （间隔越小，分析越精细，但耗时越长）
              </span>
            </el-form-item>
          </el-form>
        </div>

        <!-- 操作按钮 -->
        <div v-if="selectedFile" class="action-buttons">
          <el-button @click="resetUpload">重新选择</el-button>
          <el-button
            type="primary"
            :loading="uploading"
            @click="startUploadAndAnalysis"
          >
            开始分析
          </el-button>
        </div>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploading" class="progress-section">
        <el-icon class="progress-icon"><upload-filled /></el-icon>
        <h3>上传中...</h3>
        <el-progress
          :percentage="uploadProgress"
          :stroke-width="20"
          :text-inside="true"
        />
        <p class="progress-text">{{ uploadProgress }}%</p>
      </div>

      <!-- 分析中（会自动跳转到分析页面） -->
      <div v-if="analyzing" class="analyzing-section">
        <el-icon class="analyzing-icon"><loading /></el-icon>
        <h3>准备开始分析...</h3>
        <p>正在跳转到分析页面</p>
      </div>
    </el-card>

    <!-- 使用说明 -->
    <el-card class="tips-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><InfoFilled /></el-icon>
          <span>使用提示</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item color="#409eff">
          <h4>1. 录制视频</h4>
          <p>确保拍摄角度能清晰看到投篮动作全过程，建议从右侧拍摄</p>
        </el-timeline-item>
        <el-timeline-item color="#67c23a">
          <h4>2. 上传视频</h4>
          <p>选择清晰度适中的视频，过大的文件会增加上传时间</p>
        </el-timeline-item>
        <el-timeline-item color="#e6a23c">
          <h4>3. 等待分析</h4>
          <p>AI会自动识别关键动作，分析通常需要1-3分钟</p>
        </el-timeline-item>
        <el-timeline-item color="#f56c6c">
          <h4>4. 查看结果</h4>
          <p>获取详细的动作分析报告</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { uploadVideo, startAnalysis } from '@/api/analysis'

const router = useRouter()

const uploadRef = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const analyzing = ref(false)
const uploadProgress = ref(0)
const options = ref({
  frame_interval: 5,
  sport_type: 'basketball',
  analysis_name: '' // 用户自定义名称
})

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
  // 自动从文件名提取建议名称（去掉扩展名）
  if (file.raw && !options.value.analysis_name) {
    const fileName = file.raw.name
    const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.')) || fileName
    // 清理文件名中的特殊字符
    options.value.analysis_name = nameWithoutExt.replace(/[^a-zA-Z0-9\u4e00-\u9fa5-_]/g, '_')
  }
}

// 自动生成名称
const generateName = () => {
  const now = new Date()
  const dateStr = now.toLocaleDateString('zh-CN').replace(/\//g, '')
  const timeStr = now.toLocaleTimeString('zh-CN', { hour12: false }).replace(/:/g, '')
  options.value.analysis_name = `投篮分析_${dateStr}_${timeStr}`
}

// 生成唯一的分析ID
const generateAnalysisId = (customName) => {
  const timestamp = new Date().toISOString()
    .replace(/[-:]/g, '')
    .replace('T', '_')
    .split('.')[0]
  
  if (customName && customName.trim()) {
    // 清理用户输入的名称，只保留字母、数字、中文、下划线和短横线
    const cleanName = customName.trim()
      .replace(/\s+/g, '_') // 空格转下划线
      .replace(/[^a-zA-Z0-9\u4e00-\u9fa5_-]/g, '') // 移除特殊字符
      .substring(0, 50) // 限制长度
    
    return `${cleanName}_${timestamp}`
  }
  
  // 如果没有自定义名称，使用默认格式
  return `analysis_${timestamp}`
}

// 上传前验证
const beforeUpload = (file) => {
  const isVideo = file.type.startsWith('video/')
  const isLt500M = file.size / 1024 / 1024 < 500

  if (!isVideo) {
    ElMessage.error('只能上传视频文件!')
    return false
  }
  if (!isLt500M) {
    ElMessage.error('视频大小不能超过 10MB!')
    return false
  }
  return true
}

// 重置上传
const resetUpload = () => {
  selectedFile.value = null
  uploadProgress.value = 0
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 开始上传和分析
const startUploadAndAnalysis = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择视频文件')
    return
  }

  try {
    // 1. 上传视频
    uploading.value = true
    uploadProgress.value = 0

    const uploadRes = await uploadVideo(selectedFile.value, (percent) => {
      uploadProgress.value = percent
    })

    ElMessage.success('上传成功！')
    console.log('上传结果:', uploadRes)

    // 2. 开始分析
    analyzing.value = true
    uploading.value = false

    // 生成唯一的分析ID
    const analysisId = generateAnalysisId(options.value.analysis_name)

    const analysisData = {
      file_id: uploadRes.data.file_id,
      file_path: uploadRes.data.file_path,
      analysis_name: options.value.analysis_name || '',
      analysis_id: analysisId, // 传递自定义的分析ID
      options: {
        frame_interval: options.value.frame_interval,
        sport_type: options.value.sport_type,
        analysis_name: options.value.analysis_name,
        analysis_id: analysisId
      }
    }

    const analysisRes = await startAnalysis(analysisData)
    console.log('分析任务创建:', analysisRes)

    // 3. 跳转到分析进度页面
    router.push(`/analysis/${analysisRes.data.task_id}`)
  } catch (error) {
    console.error('上传或分析失败:', error)
    ElMessage.error('操作失败，请重试')
    uploading.value = false
    analyzing.value = false
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.upload-page {
  max-width: 900px;
  margin: 0 auto;
}

.upload-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.upload-area {
  padding: 20px;
}

.upload-dragger {
  width: 100%;
}

.file-info {
  margin-top: 20px;
}

.options-section {
  margin-top: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.options-section h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  margin-top: 30px;
  text-align: center;
}

.action-buttons .el-button {
  min-width: 120px;
}

.progress-section,
.analyzing-section {
  padding: 60px 20px;
  text-align: center;
}

.progress-icon,
.analyzing-icon {
  font-size: 64px;
  color: #409eff;
  margin-bottom: 20px;
}

.analyzing-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-section h3,
.analyzing-section h3 {
  margin: 10px 0;
  color: #303133;
}

.progress-text {
  margin-top: 10px;
  color: #909399;
  font-size: 14px;
}

.tips-card {
  margin-bottom: 20px;
}

.tips-card h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.tips-card p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .upload-area {
    padding: 10px;
  }

  .options-section {
    padding: 15px;
  }

  .el-form :deep(.el-form-item__label) {
    width: 100px !important;
  }

  .form-tip {
    display: block;
    margin-left: 0;
    margin-top: 5px;
  }
}
</style>
