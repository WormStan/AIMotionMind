import axios from 'axios'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000, // 5分钟超时（视频上传可能需要较长时间）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    NProgress.start()
    return config
  },
  (error) => {
    NProgress.done()
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    NProgress.done()
    
    const res = response.data
    
    // 如果返回的状态码不是200，则认为是错误
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    
    return res
  },
  (error) => {
    NProgress.done()
    
    console.error('响应错误:', error)
    
    let message = '请求失败'
    
    if (error.response) {
      // 服务器返回了错误响应
      message = error.response.data.message || `错误 ${error.response.status}`
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      message = '网络错误，请检查网络连接'
    } else {
      // 其他错误
      message = error.message || '未知错误'
    }
    
    ElMessage.error(message)
    
    return Promise.reject(error)
  }
)

export default request
