import type { AlertDetailResult, AlertItem, AlertStatus } from '@/types/alert'
import { request } from '@/utils/request'
import { useMockApi } from '@/api/env'
import { mockGetAlertDetail, mockGetAlerts, mockHandleAlert } from '@/mock/alert'

export async function getAlerts(payload?: { status?: AlertStatus }): Promise<AlertItem[]> {
  if (useMockApi()) return mockGetAlerts(payload)
  return request({ url: '/alert/list', method: 'GET', params: payload })
}

export async function handleAlert(payload: { id: string }): Promise<void> {
  if (useMockApi()) return mockHandleAlert(payload)
  return request({ url: '/alert/handle', method: 'POST', data: payload })
}

export async function getAlertDetail(payload: { id: string; size?: number }): Promise<AlertDetailResult> {
  if (useMockApi()) return mockGetAlertDetail(payload)
  return request({ url: `/alert/${payload.id}/detail`, method: 'GET', params: { size: payload.size } })
}
