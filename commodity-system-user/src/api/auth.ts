import type { UserInfo } from '@/types/user'
import { request } from '@/utils/request'
import { useMockApi } from '@/api/env'
import { mockGetUserInfo, mockLogin, mockRegister } from '@/mock/auth'

export async function login(payload: { username: string; password: string }): Promise<{ token: string; userInfo: UserInfo }> {
  if (useMockApi()) return mockLogin(payload)
  return request({ url: '/auth/login', method: 'POST', data: payload })
}

export async function register(payload: { username: string; password: string; phone?: string }): Promise<void> {
  if (useMockApi()) return mockRegister(payload)
  return request({ url: '/auth/register', method: 'POST', data: payload })
}

export async function getUserInfo(): Promise<UserInfo> {
  if (useMockApi()) return mockGetUserInfo()
  return request({ url: '/auth/me', method: 'GET' })
}

