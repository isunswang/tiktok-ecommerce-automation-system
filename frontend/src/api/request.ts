import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.response?.data?.message

    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
    } else if (status === 403) {
      ElMessage.error('没有权限访问该资源')
    } else if (status === 404) {
      ElMessage.error('请求的资源不存在')
    } else if (status === 422) {
      const errors = error.response?.data?.detail
      if (Array.isArray(errors)) {
        ElMessage.error(errors.map((e: any) => e.msg).join('; '))
      } else {
        ElMessage.error(message || '请求参数错误')
      }
    } else if (status >= 500) {
      ElMessage.error('服务器内部错误')
    } else {
      ElMessage.error(message || error.message || '网络错误')
    }

    return Promise.reject(error)
  },
)

export default service
