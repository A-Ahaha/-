import type { SystemConfig, SystemLogItem } from '@/types/system'
import type { UserInfo, UserRole } from '@/types/user'
import { delay, makeId, nowISO } from '@/mock/utils'
import { mockSystemConfig, mockSystemLogs, mockUsers } from '@/mock/state'

export async function mockGetUsers(payload?: { keyword?: string }): Promise<UserInfo[]> {
  await delay(320)
  const keyword = (payload?.keyword ?? '').trim()
  if (!keyword) return mockUsers.slice()
  return mockUsers.filter((u) => u.username.includes(keyword) || (u.email ?? '').includes(keyword))
}

export async function mockCreateUser(payload: {
  username: string
  email?: string
  role: UserRole
  status: UserInfo['status']
}): Promise<UserInfo> {
  await delay(420)
  const username = payload.username.trim()
  if (!username) throw new Error('用户名不能为空')
  if (mockUsers.some((u) => u.username === username)) throw new Error('用户名已存在')

  const user: UserInfo = {
    id: makeId('u'),
    username,
    role: payload.role,
    email: payload.email?.trim() || undefined,
    status: payload.status,
  }
  mockUsers.unshift(user)
  mockSystemLogs.unshift({ id: makeId('log'), level: 'info', message: `创建用户：${username}`, createdAt: nowISO() })
  return user
}

export async function mockUpdateUser(payload: {
  id: string
  email?: string
  status: UserInfo['status']
}): Promise<UserInfo> {
  await delay(420)
  const user = mockUsers.find((u) => u.id === payload.id)
  if (!user) throw new Error('用户不存在')
  user.email = payload.email?.trim() || undefined
  user.status = payload.status
  mockSystemLogs.unshift({ id: makeId('log'), level: 'info', message: `更新用户：${user.username}`, createdAt: nowISO() })
  return user
}

export async function mockDeleteUser(payload: { id: string }): Promise<void> {
  await delay(420)
  const idx = mockUsers.findIndex((u) => u.id === payload.id)
  if (idx < 0) throw new Error('用户不存在')
  const [user] = mockUsers.splice(idx, 1)
  mockSystemLogs.unshift({ id: makeId('log'), level: 'warn', message: `删除用户：${user.username}`, createdAt: nowISO() })
}

export async function mockAssignRole(payload: { id: string; role: UserRole }): Promise<UserInfo> {
  await delay(360)
  const user = mockUsers.find((u) => u.id === payload.id)
  if (!user) throw new Error('用户不存在')
  user.role = payload.role
  mockSystemLogs.unshift({
    id: makeId('log'),
    level: 'info',
    message: `分配角色：${user.username} → ${payload.role}`,
    createdAt: nowISO(),
  })
  return user
}

export async function mockGetSystemConfig(): Promise<SystemConfig> {
  await delay(260)
  return { ...mockSystemConfig }
}

export async function mockUpdateSystemConfig(payload: SystemConfig): Promise<SystemConfig> {
  await delay(420)
  if (payload.collectFrequencyMinutes <= 0) throw new Error('采集频率必须大于 0')
  if (payload.collectMaxPages <= 0) throw new Error('采集最大页数必须大于 0')
  if (payload.alertThreshold < 1 || payload.alertThreshold > 100) throw new Error('预警阈值需在 1-100 之间')
  mockSystemConfig.collectFrequencyMinutes = payload.collectFrequencyMinutes
  mockSystemConfig.collectEnabled = payload.collectEnabled
  mockSystemConfig.collectItemUrl = payload.collectItemUrl
  mockSystemConfig.collectSku = payload.collectSku
  mockSystemConfig.collectProductName = payload.collectProductName
  mockSystemConfig.collectIsCompetitor = payload.collectIsCompetitor
  mockSystemConfig.collectClearExisting = payload.collectClearExisting
  mockSystemConfig.collectIncludeAlerts = payload.collectIncludeAlerts
  mockSystemConfig.collectMaxPages = payload.collectMaxPages
  mockSystemConfig.alertThreshold = payload.alertThreshold
  mockSystemLogs.unshift({ id: makeId('log'), level: 'info', message: '更新系统设置', createdAt: nowISO() })
  return { ...mockSystemConfig }
}

export async function mockGetSystemLogs(payload: {
  page: number
  pageSize: number
}): Promise<{ list: SystemLogItem[]; total: number }> {
  await delay(320)
  const page = Math.max(1, Math.floor(payload.page))
  const pageSize = Math.max(1, Math.floor(payload.pageSize))
  const total = mockSystemLogs.length
  const start = (page - 1) * pageSize
  const list = mockSystemLogs.slice(start, start + pageSize)
  return { list, total }
}
