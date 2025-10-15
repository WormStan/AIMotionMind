import request from './request'

/**
 * 上传视频文件
 * @param {File} file 视频文件
 * @param {Function} onProgress 上传进度回调
 * @returns {Promise}
 */
export function uploadVideo(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('sport_type', 'basketball')

  return request({
    url: '/upload',
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    }
  })
}

/**
 * 开始分析任务
 * @param {Object} data 分析参数
 * @returns {Promise}
 */
export function startAnalysis(data) {
  return request({
    url: '/analysis/start',
    method: 'POST',
    data
  })
}

/**
 * 查询任务状态
 * @param {String} taskId 任务ID
 * @returns {Promise}
 */
export function getTaskStatus(taskId) {
  return request({
    url: `/analysis/status/${taskId}`,
    method: 'GET'
  })
}

/**
 * 获取分析结果
 * @param {String} analysisId 分析ID
 * @param {String} sportType 运动类型
 * @returns {Promise}
 */
export function getAnalysisResult(analysisId, sportType = 'basketball') {
  // 如果是curry_demo，使用特殊的API
  if (analysisId === 'curry_demo') {
    return request({
      url: '/analysis/demo/curry',
      method: 'GET'
    })
  }
  
  return request({
    url: `/analysis/result/${analysisId}`,
    method: 'GET',
    params: { sport_type: sportType }
  })
}

/**
 * 获取分析历史列表
 * @param {String} sportType 运动类型
 * @returns {Promise}
 */
export function getAnalysisList(sportType = 'basketball') {
  return request({
    url: '/analysis/list',
    method: 'GET',
    params: { sport_type: sportType }
  })
}

/**
 * 获取所有任务列表
 * @returns {Promise}
 */
export function getTaskList() {
  return request({
    url: '/analysis/tasks',
    method: 'GET'
  })
}

/**
 * 获取文件URL
 * @param {String} fileType 文件类型
 * @param {String} filename 文件路径
 * @returns {String} 文件URL
 */
export function getFileUrl(fileType, filename) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  return `${baseURL}/files/${fileType}/${filename}`
}

/**
 * 健康检查
 * @returns {Promise}
 */
export function healthCheck() {
  return request({
    url: '/health',
    method: 'GET'
  })
}
