import type { SystemConfig, SystemLogItem } from '@/types/system'
import type { UserInfo, UserRole } from '@/types/user'
import { request } from '@/utils/request'
import { useMockApi } from '@/api/env'

/** CSV 导入 / ABSA 重建 / 京东采集会跑模型推理，常需数分钟，避免沿用全局 15s 超时 */
const LONG_RUNNING_TIMEOUT_MS = 15 * 60 * 1000
import {
  mockAssignRole,
  mockCreateUser,
  mockDeleteUser,
  mockGetSystemConfig,
  mockGetSystemLogs,
  mockGetUsers,
  mockUpdateSystemConfig,
  mockUpdateUser,
} from '@/mock/admin'

export interface ProductRecord {
  id: string
  sku: string
  name: string
  platform?: string
  isCompetitor?: boolean
  createdAt?: string
}

export interface PagedProducts {
  list: ProductRecord[]
  total: number
}

export async function getUsers(payload?: { keyword?: string }): Promise<UserInfo[]> {
  if (useMockApi()) return mockGetUsers(payload)
  return request({ url: '/admin/users', method: 'GET', params: payload })
}

export async function createUser(payload: {
  username: string
  email?: string
  role: UserRole
  status: UserInfo['status']
}): Promise<UserInfo> {
  if (useMockApi()) return mockCreateUser(payload)
  return request({ url: '/admin/users', method: 'POST', data: payload })
}

export async function updateUser(payload: { id: string; email?: string; status: UserInfo['status'] }): Promise<UserInfo> {
  if (useMockApi()) return mockUpdateUser(payload)
  return request({ url: `/admin/users/${payload.id}`, method: 'PUT', data: payload })
}

export async function deleteUser(payload: { id: string }): Promise<void> {
  if (useMockApi()) return mockDeleteUser(payload)
  return request({ url: `/admin/users/${payload.id}`, method: 'DELETE' })
}

export async function assignRole(payload: { id: string; role: UserRole }): Promise<UserInfo> {
  if (useMockApi()) return mockAssignRole(payload)
  return request({ url: `/admin/users/${payload.id}/role`, method: 'PATCH', data: payload })
}

export async function getSystemConfig(): Promise<SystemConfig> {
  if (useMockApi()) return mockGetSystemConfig()
  return request({ url: '/admin/system/config', method: 'GET' })
}

export async function updateSystemConfig(payload: SystemConfig): Promise<SystemConfig> {
  if (useMockApi()) return mockUpdateSystemConfig(payload)
  return request({ url: '/admin/system/config', method: 'PUT', data: payload })
}

export async function testSystemNotify(): Promise<{ email?: string | null; webhook?: string | null }> {
  if (useMockApi()) return { email: 'ok(mock)', webhook: 'ok(mock)' }
  return request({ url: '/admin/system/test-notify', method: 'POST' })
}

export async function getSystemLogs(payload: {
  page: number
  pageSize: number
}): Promise<{ list: SystemLogItem[]; total: number }> {
  if (useMockApi()) return mockGetSystemLogs(payload)
  return request({ url: '/admin/system/logs', method: 'GET', params: payload })
}

export async function getProducts(payload: {
  page: number
  pageSize: number
}): Promise<PagedProducts> {
  // Mock 环境下暂时直接返回空列表
  if (useMockApi()) {
    return { list: [], total: 0 }
  }
  return request({
    url: '/admin/products',
    method: 'GET',
    params: payload,
  })
}

export async function createProduct(payload: {
  sku: string
  name: string
  platform?: string
  isCompetitor?: boolean
}): Promise<ProductRecord> {
  if (useMockApi()) {
    // Mock 环境下只做前端演示，不持久化
    const now = new Date().toISOString()
    return {
      id: `p_${now}`,
      sku: payload.sku,
      name: payload.name,
      platform: payload.platform,
      isCompetitor: payload.isCompetitor,
      createdAt: now,
    }
  }
  return request({
    url: '/admin/products',
    method: 'POST',
    data: payload,
  })
}

export async function deleteProduct(payload: { productId: number | string }): Promise<{ productId: number | string }> {
  if (useMockApi()) {
    return { productId: payload.productId }
  }
  return request({
    url: `/admin/products/${payload.productId}`,
    method: 'DELETE',
  })
}

export async function importCsvUpload(payload: {
  sku: string
  productName?: string
  isCompetitor?: boolean
  clearExisting?: boolean
  /** 默认 false：仅写库 + 规则/启发式情感（快）。true 时逐条跑 Transformer（很慢） */
  useTransformer?: boolean
  file: File
}): Promise<{ count: number; productId: number; isCompetitor: boolean }> {
  const form = new FormData()
  form.append('sku', payload.sku)
  form.append('productName', payload.productName || payload.sku)
  form.append('isCompetitor', String(Boolean(payload.isCompetitor)))
  form.append('clearExisting', String(Boolean(payload.clearExisting)))
  form.append('useTransformer', String(Boolean(payload.useTransformer)))
  form.append('file', payload.file)
  return request({
    url: '/admin/import-csv-upload',
    method: 'POST',
    data: form,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: LONG_RUNNING_TIMEOUT_MS,
  })
}

export interface RebuildAbsaResult {
  productId: number
  status: string
  rebuiltMainProductIds: number[]
  alertRebuilt: boolean
}

export async function rebuildAbsa(payload: {
  productId: number | string
  includeAlerts?: boolean
}): Promise<RebuildAbsaResult> {
  if (useMockApi()) {
    return {
      productId: Number(payload.productId) || 0,
      status: 'ok(mock)',
      rebuiltMainProductIds: [],
      alertRebuilt: Boolean(payload.includeAlerts),
    }
  }

  return request({
    url: `/admin/products/${payload.productId}/rebuild-absa`,
    method: 'POST',
    data: {
      includeAlerts: Boolean(payload.includeAlerts),
    },
    timeout: LONG_RUNNING_TIMEOUT_MS,
  })
}

export interface JdCollectResult {
  jobId?: number
  count: number
  collectedCount: number
  productId: number
  isCompetitor: boolean
  platform: string
  productName: string
  itemUrl: string
}

export async function collectJdComments(payload: {
  itemUrl: string
  sku: string
  productName?: string
  isCompetitor?: boolean
  clearExisting?: boolean
  includeAlerts?: boolean
  maxPages?: number
}): Promise<JdCollectResult> {
  if (useMockApi()) {
    return {
      count: 12,
      collectedCount: 12,
      productId: Date.now(),
      isCompetitor: Boolean(payload.isCompetitor),
      platform: 'jd',
      productName: payload.productName || payload.sku,
      itemUrl: payload.itemUrl,
    }
  }
  return request({
    url: '/admin/collect/jd',
    method: 'POST',
    data: payload,
    timeout: LONG_RUNNING_TIMEOUT_MS,
  })
}

export interface CollectJobItem {
  id: string
  platform: string
  sku: string
  productName: string
  itemUrl: string
  status: 'pending' | 'running' | 'success' | 'failed' | string
  totalCollected: number
  totalImported: number
  errorMessage: string
  startedAt: string
  finishedAt: string
}

export async function getCollectJobs(payload: {
  page: number
  pageSize: number
}): Promise<{ list: CollectJobItem[]; total: number }> {
  if (useMockApi()) {
    return {
      list: [],
      total: 0,
    }
  }
  return request({
    url: '/admin/collect/jobs',
    method: 'GET',
    params: payload,
  })
}
