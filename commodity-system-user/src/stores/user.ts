import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { UserInfo, UserRole } from '@/types/user'
import { STORAGE_SESSION_USER_ID_KEY, STORAGE_TOKEN_KEY, STORAGE_USER_KEY } from '@/constants/storage'
import { getStorage, getStorageJSON, removeStorage, setStorage, setStorageJSON } from '@/utils/storage'
import { getUserInfo as getUserInfoApi, login as loginApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)
  const role = computed<UserRole | ''>(() => userInfo.value?.role ?? '')
  const isLoggedIn = computed(() => Boolean(token.value))

  function restore() {
    token.value = getStorage(STORAGE_TOKEN_KEY) ?? ''
    userInfo.value = getStorageJSON<UserInfo>(STORAGE_USER_KEY)
  }

  async function login(payload: { username: string; password: string }) {
    const res = await loginApi(payload)
    token.value = res.token
    userInfo.value = res.userInfo
    setStorage(STORAGE_TOKEN_KEY, res.token)
    setStorageJSON(STORAGE_USER_KEY, res.userInfo)
    setStorage(STORAGE_SESSION_USER_ID_KEY, res.userInfo.id)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    removeStorage(STORAGE_TOKEN_KEY)
    removeStorage(STORAGE_USER_KEY)
    removeStorage(STORAGE_SESSION_USER_ID_KEY)
  }

  async function getUserInfo() {
    if (!token.value) return null
    const res = await getUserInfoApi()
    userInfo.value = res
    setStorageJSON(STORAGE_USER_KEY, res)
    return res
  }

  return { token, userInfo, role, isLoggedIn, restore, login, logout, getUserInfo }
})

