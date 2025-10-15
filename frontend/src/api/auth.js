/**
 * 认证相关API
 */
import request from './request'

/**
 * 验证设备
 */
export function verifyDevice(deviceId) {
  return request({
    url: '/auth/verify',
    method: 'post',
    data: {
      device_id: deviceId
    }
  })
}

/**
 * 获取用户历史记录
 */
export function getUserHistory() {
  return request({
    url: '/auth/history',
    method: 'get'
  })
}

/**
 * 获取用户统计信息
 */
export function getUserStats() {
  return request({
    url: '/auth/stats',
    method: 'get'
  })
}
