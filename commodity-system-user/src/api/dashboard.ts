import type { CommentItem, PagedCommentResult, QualityIssueTopItem, TrendPoint } from '@/types/dashboard'
import { request } from '@/utils/request'
import { useMockApi } from '@/api/env'
import { mockGetLatestComments, mockGetTopIssues, mockGetTrendData } from '@/mock/dashboard'

export async function getTopIssues(): Promise<QualityIssueTopItem[]> {
  if (useMockApi()) return mockGetTopIssues()
  return request({ url: '/dashboard/top-issues', method: 'GET' })
}

export async function getTrendData(payload?: { days?: number }): Promise<TrendPoint[]> {
  if (useMockApi()) return mockGetTrendData(payload)
  return request({ url: '/dashboard/trend', method: 'GET', params: payload })
}

export async function getLatestComments(payload?: { size?: number }): Promise<CommentItem[]> {
  if (useMockApi()) return mockGetLatestComments(payload)
  return request({ url: '/dashboard/comments', method: 'GET', params: payload })
}

export async function getAllComments(payload: { page: number; pageSize: number }): Promise<PagedCommentResult> {
  if (useMockApi()) {
    const full = await mockGetLatestComments({ size: 30 })
    const start = (payload.page - 1) * payload.pageSize
    return {
      list: full.slice(start, start + payload.pageSize),
      total: full.length,
    }
  }
  return request({ url: '/dashboard/comments-page', method: 'GET', params: payload })
}

