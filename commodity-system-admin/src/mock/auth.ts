import type { UserInfo } from '@/types/user'
import { delay, makeId } from '@/mock/utils'
import { mockPasswords, mockTokenToUserId, mockUsers } from '@/mock/state'
import { STORAGE_SESSION_USER_ID_KEY, STORAGE_TOKEN_KEY } from '@/constants/storage'
import { getStorage, setStorage } from '@/utils/storage'

export async function mockLogin(payload: { username: string; password: string }): Promise<{ token: string; userInfo: UserInfo }> {
  await delay()
  const { username, password } = payload
  const user = mockUsers.find((u) => u.username === username)
  if (!user) throw new Error('账号不存在')
  if (mockPasswords[username] !== password) throw new Error('账号或密码错误')
  if (user.role !== 'admin') throw new Error('当前账号无管理端权限')

  const token = makeId('token')
  mockTokenToUserId.set(token, user.id)
  setStorage(STORAGE_SESSION_USER_ID_KEY, user.id)
  return { token, userInfo: user }
}

export async function mockGetUserInfo(): Promise<UserInfo> {
  await delay(260)
  const token = getStorage(STORAGE_TOKEN_KEY)
  if (!token) throw new Error('未登录')
  const userId = getStorage(STORAGE_SESSION_USER_ID_KEY) || mockTokenToUserId.get(token)
  if (!userId) throw new Error('登录已失效，请重新登录')
  const user = mockUsers.find((u) => u.id === userId)
  if (!user) throw new Error('用户不存在')
  return user
}
