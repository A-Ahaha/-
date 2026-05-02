import type { BatchTrendResponse, IssueDetail, PagedComments } from '@/types/detail'
import { request } from '@/utils/request'
import { useMockApi } from '@/api/env'
import { mockGetBatchTrend, mockGetComments, mockGetDetailById } from '@/mock/detail'

export async function getDetailById(payload: { id: string }): Promise<IssueDetail> {
  if (useMockApi()) return mockGetDetailById(payload)
  return request({ url: `/detail/${payload.id}`, method: 'GET' })
}

export async function getComments(payload: {
  id: string
  page: number
  pageSize: number
}): Promise<PagedComments> {
  if (useMockApi()) return mockGetComments(payload)
  return request({ url: `/detail/${payload.id}/comments`, method: 'GET', params: payload })
}

export async function getBatchTrend(payload: {
  id: string
  days?: number
  topBatches?: number
}): Promise<BatchTrendResponse> {
  if (useMockApi()) return mockGetBatchTrend(payload)
  return request({
    url: `/detail/${payload.id}/batch-trend`,
    method: 'GET',
    params: {
      days: payload.days,
      topBatches: payload.topBatches,
    },
  })
}

