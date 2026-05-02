import type { UserInfo } from '@/types/user'
import { delay, makeId } from '@/mock/utils'
import { loadDb, saveDb } from '@/mock/db'
import { STORAGE_SESSION_USER_ID_KEY, STORAGE_TOKEN_KEY } from '@/constants/storage'
import { getStorage, setStorage } from '@/utils/storage'

function safeUser(u: UserInfo & { password?: string }): UserInfo {
  const clone = { ...(u as any) } as Record<string, unknown>
  delete clone.password
  return clone as unknown as UserInfo
}

export async function mockLogin(payload: { username: string; password: string }): Promise<{ token: string; userInfo: UserInfo }> {
  await delay()
  const { username, password } = payload
  const db = loadDb()
  const user = db.users.find((u) => u.username === username)
  if (!user) throw new Error('账号不存在')
  if (user.password !== password) throw new Error('账号或密码错误')
  if (user.status !== 'active') throw new Error('账号已被禁用')

  const token = makeId('token')
  setStorage(STORAGE_TOKEN_KEY, token)
  setStorage(STORAGE_SESSION_USER_ID_KEY, user.id)
  return { token, userInfo: safeUser(user) }
}

export async function mockRegister(payload: { username: string; password: string; phone?: string }): Promise<void> {
  await delay(520)
  const db = loadDb()
  const username = payload.username.trim()
  if (!username) throw new Error('用户名不能为空')
  if (db.users.some((u) => u.username === username)) throw new Error('用户名已存在')
  if (payload.password.length < 6) throw new Error('密码至少 6 位')

  db.users.unshift({
    id: makeId('u'),
    username,
    role: 'user',
    phone: payload.phone?.trim() || undefined,
    status: 'active',
    password: payload.password,
  })
  saveDb(db)
}

export async function mockGetUserInfo(): Promise<UserInfo> {
  await delay(260)
  const userId = getStorage(STORAGE_SESSION_USER_ID_KEY)
  if (!userId) throw new Error('未登录')
  const db = loadDb()
  const user = db.users.find((u) => u.id === userId)
  if (!user) throw new Error('登录已失效，请重新登录')
  return safeUser(user)
}
