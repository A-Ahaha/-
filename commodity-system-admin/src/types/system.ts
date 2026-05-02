export interface SystemConfig {
  collectFrequencyMinutes: number
  collectEnabled: boolean
  collectItemUrl: string
  collectSku: string
  collectProductName: string
  collectIsCompetitor: boolean
  collectClearExisting: boolean
  collectIncludeAlerts: boolean
  collectMaxPages: number
  alertThreshold: number
  emailEnabled: boolean
  emailTo: string
  smtpHost: string
  smtpPort: number
  smtpUser: string
  smtpPassword: string
  smtpUseSsl: boolean
  webhookEnabled: boolean
  webhookUrl: string
}

export interface SystemLogItem {
  id: string
  level: 'info' | 'warn' | 'error'
  message: string
  createdAt: string
}
