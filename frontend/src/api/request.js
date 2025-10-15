import axios from 'axios'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import { getDeviceId } from '@/utils/device'

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
    
    // 自动添加设备ID到请求头
    const deviceId = getDeviceId()
    config.headers['X-Device-ID'] = deviceId
    
    // 如果是POST请求且有body
    if (config.method === 'post' && config.data) {
      // 判断是否是FormData（文件上传）
      if (config.data instanceof FormData) {
        // FormData对象，直接append
        config.data.append('device_id', deviceId)
      } else {
        // 普通JSON对象，添加到data中
        config.data = {
          ...config.data,
          device_id: deviceId
        }
      }
    }
    
    // 如果是GET请求，添加到查询参数
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        device_id: deviceId
      }
    }
    
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
