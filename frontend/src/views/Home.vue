<template>
  <div class="home-page">
    <el-card class="hero-card" shadow="hover">
      <div class="hero-content">
        <h1 class="hero-title">
          <el-icon class="hero-icon"><Basketball /></el-icon>
          AIMotionMind - 慧动分析
        </h1>
        <p class="hero-subtitle">篮球投篮动作AI分析系统</p>
        <p class="hero-description">
          利用先进的AI技术，精确分析你的投篮动作，
          提供专业的姿势评估和改进建议
        </p>
        <el-button
          type="primary"
          size="large"
          class="upload-btn"
          @click="goToUpload"
        >
          <el-icon><Upload /></el-icon>
          开始分析
        </el-button>
      </div>
    </el-card>

    <!-- 明星案例展示 -->
    <el-card class="star-case-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>
            <el-icon style="margin-right: 8px;"><TrophyBase /></el-icon>
            明星案例 - 看看AI如何分析投篮动作
          </span>
        </div>
      </template>
      
      <div class="star-case-content">
        <el-row :gutter="24">
          <el-col :xs="24" :md="8">
            <div class="case-image-wrapper">
              <img 
                src="/star_report/curry/keyframes/keyframe_release.jpg" 
                alt="库里投篮"
                class="case-image"
                @error="handleImageError"
              />
              <div class="case-badge">
                <el-tag type="warning" effect="dark" size="large">
                  <el-icon><Star /></el-icon>
                  NBA球星
                </el-tag>
              </div>
            </div>
          </el-col>
          
          <el-col :xs="24" :md="16">
            <div class="case-info">
              <h2 class="case-title">
                <el-icon class="title-icon"><Basketball /></el-icon>
                斯蒂芬·库里 投篮动作分析
              </h2>
              <p class="case-description">
                查看NBA历史最伟大射手之一的投篮动作分析报告，了解AIMotionMind如何精确捕捉和分析每一个关键动作细节。
              </p>
              
              <div class="case-stats">
                <el-space :size="20" wrap>
                  <div class="stat-item">
                    <el-icon color="#409eff"><VideoCamera /></el-icon>
                    <span>投篮分析</span>
                  </div>
                  <div class="stat-item">
                    <el-icon color="#67c23a"><Camera /></el-icon>
                    <span>关键动作节点</span>
                  </div>
                  <div class="stat-item">
                    <el-icon color="#e6a23c"><DataAnalysis /></el-icon>
                    <span>多维度指标</span>
                  </div>
                </el-space>
              </div>
              
              <div class="case-actions">
                <el-button 
                  type="primary" 
                  size="large"
                  @click="viewStarCase"
                  :icon="View"
                >
                  查看完整分析报告
                </el-button>
                <el-button 
                  size="large"
                  @click="goToUpload"
                >
                  分析我的投篮
                </el-button>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { View, Star, TrophyBase } from '@element-plus/icons-vue'

const router = useRouter()

const goToUpload = () => {
  router.push('/upload')
}

const viewStarCase = () => {
  // 跳转到前端Result页面查看curry示例
  router.push('/result/curry_demo')
}

const handleImageError = (e) => {
  // 如果图片加载失败，使用占位图
  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTgiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7lupTph4fotYTmoYg8L3RleHQ+PC9zdmc+'
}
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.hero-card {
  margin-bottom: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.hero-card :deep(.el-card__body) {
  padding: 60px 40px;
}

.hero-content {
  text-align: center;
}

.hero-title {
  font-size: 48px;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-icon {
  font-size: 54px;
  margin-right: 15px;
}

.hero-subtitle {
  font-size: 24px;
  margin: 0 0 20px 0;
  opacity: 0.9;
}

.hero-description {
  font-size: 16px;
  margin: 0 0 30px 0;
  opacity: 0.8;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.upload-btn {
  font-size: 18px;
  padding: 15px 40px;
  border-radius: 25px;
}

.features {
  margin-bottom: 30px;
}

.feature-card {
  text-align: center;
  padding: 20px;
  margin-bottom: 20px;
  transition: transform 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.feature-card h3 {
  margin: 10px 0;
  font-size: 20px;
  color: #303133;
}

.feature-card p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .hero-card :deep(.el-card__body) {
    padding: 30px 20px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .hero-description {
    font-size: 14px;
  }

  .upload-btn {
    font-size: 16px;
    padding: 12px 30px;
  }
}

/* 明星案例样式 */
.star-case-card {
  margin-bottom: 30px;
  overflow: hidden;
}

.star-case-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
  color: white;
  font-weight: bold;
  font-size: 18px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.star-case-content {
  padding: 20px 0;
}

.case-image-wrapper {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s;
}

.case-image-wrapper:hover {
  transform: scale(1.02);
}

.case-image {
  width: 100%;
  height: auto;
  display: block;
  object-fit: cover;
  min-height: 300px;
}

.case-badge {
  position: absolute;
  top: 15px;
  right: 15px;
}

.case-info {
  padding: 0 20px;
}

.case-title {
  font-size: 28px;
  color: #303133;
  margin: 0 0 15px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 32px;
  color: #e6a23c;
}

.case-description {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 20px;
}

.case-stats {
  margin-bottom: 25px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  color: #606266;
  font-weight: 500;
}

.case-actions {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

/* 移动端适配 - 明星案例 */
@media (max-width: 768px) {
  .case-info {
    padding: 20px 0 0 0;
  }

  .case-title {
    font-size: 22px;
  }

  .case-description {
    font-size: 14px;
  }

  .case-actions {
    flex-direction: column;
  }

  .case-actions .el-button {
    width: 100%;
  }

  .case-image {
    min-height: 200px;
  }
}
</style>
