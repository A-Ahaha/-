import type { TrendPoint, CommentItem } from '@/types/dashboard'

export interface CompetitorCompareItem {
  brand: string
  displayName: string
  role: 'main' | 'competitor'
  mentions: number
  sentiment: number
}

export interface IssueDetail {
  id: string
  name: string
  mentions: number
  sentiment: number
  severity: 1 | 2 | 3 | 4 | 5
  productName: string
  trend: TrendPoint[]
  competitors: CompetitorCompareItem[]
}

export interface PagedComments {
  list: CommentItem[]
  total: number
}

export interface BatchTrendItem {
  batchName: string
  mentions: number
  changePct: number | null
  series: number[]
}

export interface BatchTrendResponse {
  date: string[]
  batches: BatchTrendItem[]
}

