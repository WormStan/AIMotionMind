/**
 * 设备ID管理工具
 * 用于游客模式的用户识别
 */

const DEVICE_ID_KEY = 'aimotion_device_id'

/**
 * 生成UUID
 */
function generateUUID() {
  return 'guest_' + 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

/**
 * 获取或创建设备ID
 */
export function getDeviceId() {
  let deviceId = localStorage.getItem(DEVICE_ID_KEY)
  
  if (!deviceId) {
    deviceId = generateUUID()
    localStorage.setItem(DEVICE_ID_KEY, deviceId)
    console.log('🆕 新设备ID已创建:', deviceId)
  } else {
    console.log('✅ 设备ID已存在:', deviceId)
  }
  
  return deviceId
}

/**
 * 清除设备ID（用于测试或重置）
 */
export function clearDeviceId() {
  localStorage.removeItem(DEVICE_ID_KEY)
  console.log('🗑️ 设备ID已清除')
}

/**
 * 获取设备信息（用于调试）
 */
export function getDeviceInfo() {
  const deviceId = getDeviceId()
  const userAgent = navigator.userAgent
  const platform = navigator.platform
  const language = navigator.language
  
  return {
    deviceId,
    userAgent,
    platform,
    language,
    createdAt: localStorage.getItem(DEVICE_ID_KEY + '_created') || new Date().toISOString()
  }
}

/**
 * 验证设备ID（调用后端API）
 */
export async function verifyDevice(deviceId) {
  try {
    const response = await fetch('/api/auth/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Device-ID': deviceId
      },
      body: JSON.stringify({ device_id: deviceId })
    })
    
    const result = await response.json()
    
    if (result.code === 200) {
      console.log('✅ 设备验证成功:', result.data)
      return result.data
    } else {
      console.error('❌ 设备验证失败:', result.message)
      return null
    }
  } catch (error) {
    console.error('❌ 设备验证异常:', error)
    return null
  }
}
