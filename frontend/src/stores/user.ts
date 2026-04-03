import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'
import router from '@/router'

interface UserInfo {
  id: string  // UUID是字符串类型
  username: string
  nickname: string
  avatar?: string  // 可选字段
  role: string
  is_active?: boolean
  created_at?: string
}

interface LoginParams {
  username: string
  password: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res = await request.post('/v1/auth/login', { username, password })
    const data = res.data || res
    token.value = data.access_token || data.token
    localStorage.setItem('token', token.value)
    await fetchUserInfo()
  }

  async function fetchUserInfo() {
    try {
      const res = await request.get('/v1/auth/me')
      const data = res.data || res
      userInfo.value = data
      localStorage.setItem('userInfo', JSON.stringify(data))
    } catch {
      userInfo.value = null
    }
  }

  async function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    router.push({ name: 'Login' })
  }

  function initUserInfo() {
    const stored = localStorage.getItem('userInfo')
    if (stored) {
      try {
        userInfo.value = JSON.parse(stored)
      } catch {
        userInfo.value = null
      }
    }
  }

  if (token.value) {
    initUserInfo()
  }

  return { token, userInfo, isLoggedIn, login, fetchUserInfo, logout }
})
