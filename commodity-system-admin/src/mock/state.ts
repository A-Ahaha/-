import type { AlertItem } from '@/types/alert'
import type { SystemConfig, SystemLogItem } from '@/types/system'
import type { UserInfo } from '@/types/user'

export const mockPasswords: Record<string, string> = {
  admin: 'admin123',
  demo: 'demo123',
}

export const mockUsers: UserInfo[] = [
  { id: 'u_admin', username: 'admin', role: 'admin', email: 'admin@local.test', status: 'active' },
  { id: 'u_demo', username: 'demo', role: 'user', email: 'demo@local.test', status: 'active' },
]

export const mockTokenToUserId = new Map<string, string>()

export const mockSystemConfig: SystemConfig = {
  collectFrequencyMinutes: 30,
  collectEnabled: false,
  collectItemUrl: '',
  collectSku: '',
  collectProductName: '',
  collectIsCompetitor: false,
  collectClearExisting: false,
  collectIncludeAlerts: false,
  collectMaxPages: 20,
  alertThreshold: 80,
  emailEnabled: false,
  emailTo: '',
  smtpHost: '',
  smtpPort: 465,
  smtpUser: '',
  smtpPassword: '',
  smtpUseSsl: true,
  webhookEnabled: false,
  webhookUrl: '',
}

export const mockAlerts: AlertItem[] = [
  {
    id: 'a_1001',
    issueName: '包装破损',
    rule: '近24小时提及次数 > 120',
    triggeredAt: '2026-03-24T08:12:00.000Z',
    status: 'pending',
  },
  {
    id: 'a_1002',
    issueName: '异味明显',
    rule: '负面情绪强度 > 0.72',
    triggeredAt: '2026-03-24T14:26:00.000Z',
    status: 'pending',
  },
  {
    id: 'a_1003',
    issueName: '漏液',
    rule: '近7天环比增长 > 35%',
    triggeredAt: '2026-03-23T21:05:00.000Z',
    status: 'handled',
  },
]

export const mockSystemLogs: SystemLogItem[] = Array.from({ length: 48 }).map((_, idx) => {
  const level = idx % 11 === 0 ? 'error' : idx % 7 === 0 ? 'warn' : 'info'
  return {
    id: `log_${idx + 1}`,
    level,
    message:
      level === 'error'
        ? '接口请求失败：上游服务不可用'
        : level === 'warn'
          ? '预警阈值接近上限'
          : '数据采集任务执行完成',
    createdAt: new Date(Date.now() - idx * 60 * 60 * 1000).toISOString(),
  }
})
