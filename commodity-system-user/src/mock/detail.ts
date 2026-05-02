import type { BatchTrendResponse, IssueDetail, PagedComments } from '@/types/detail'
import { delay } from '@/mock/utils'
import { loadDb } from '@/mock/db'

export async function mockGetDetailById(payload: { id: string }): Promise<IssueDetail> {
  await delay(360)
  const db = loadDb()
  const issue = db.issues.find((i) => i.id === payload.id)
  if (!issue) throw new Error('数据不存在')
  return {
    id: issue.id,
    name: issue.name,
    mentions: issue.mentions,
    sentiment: issue.sentiment,
    severity: issue.severity,
    productName: '示例主商品',
    trend: issue.trend,
    competitors: issue.competitors.map((c) => ({
      brand: c.brand,
      displayName: c.brand === '本品' ? '主商品：示例主商品' : `竞品：${c.brand}`,
      role: c.brand === '本品' ? 'main' : 'competitor',
      mentions: c.mentions,
      sentiment: c.sentiment,
    })),
  }
}

export async function mockGetComments(payload: {
  id: string
  page: number
  pageSize: number
}): Promise<PagedComments> {
  await delay(340)
  const db = loadDb()
  const issue = db.issues.find((i) => i.id === payload.id)
  if (!issue) throw new Error('数据不存在')
  const page = Math.max(1, Math.floor(payload.page))
  const pageSize = Math.max(1, Math.floor(payload.pageSize))
  const total = issue.comments.length
  const start = (page - 1) * pageSize
  const list = issue.comments.slice(start, start + pageSize)
  return { list, total }
}

export async function mockGetBatchTrend(payload: { id: string; days?: number; topBatches?: number }): Promise<BatchTrendResponse> {
  await delay(260)
  const db = loadDb()
  const issue = db.issues.find((i) => i.id === payload.id)
  if (!issue) throw new Error('数据不存在')

  const days = payload.days ?? 14
  const topBatches = payload.topBatches ?? 5

  // 用固定“批次A/B/C”模拟批次维度；系列形状按 issue.trend 做缩放，避免页面完全静态。
  const date = issue.trend.slice(-days).map((t) => t.date)
  const baseSeries = issue.trend.slice(-days).map((t) => t.value)

  const allBatches = [
    { batchName: '批次A', factor: 1.0 },
    { batchName: '批次B', factor: 0.72 },
    { batchName: '批次C', factor: 0.48 },
    { batchName: '批次D', factor: 0.34 },
    { batchName: '批次E', factor: 0.26 },
  ].slice(0, Math.max(1, topBatches))

  const batches = allBatches.map((b) => {
    const series = baseSeries.map((v) => Math.max(0, Math.round(v * b.factor * (0.85 + (v % 7) * 0.02))))
    const mid = Math.floor(series.length / 2)
    const first = series.slice(0, mid).reduce((a, c) => a + c, 0)
    const last = series.slice(mid).reduce((a, c) => a + c, 0)
    const changePct = first > 0 ? round2(((last - first) / first) * 100) : null
    const mentions = series.reduce((a, c) => a + c, 0)
    return { batchName: b.batchName, mentions, changePct, series }
  })

  return { date, batches }
}

function round2(n: number) {
  return Math.round(n * 100) / 100
}

