import type { UserInfo } from '@/types/user'
import type { CommentItem, QualityIssueTopItem, TrendPoint } from '@/types/dashboard'
import type { CompetitorCompareItem } from '@/types/detail'
import { STORAGE_MOCK_DB_KEY } from '@/constants/storage'
import { getStorageJSON, setStorageJSON } from '@/utils/storage'

export interface MockDbIssue {
  id: string
  name: string
  mentions: number
  sentiment: number
  severity: 1 | 2 | 3 | 4 | 5
  trend: TrendPoint[]
  competitors: CompetitorCompareItem[]
  comments: CommentItem[]
}

export interface MockDbData {
  users: Array<UserInfo & { password: string }>
  issues: MockDbIssue[]
}

function seedIssues(): MockDbIssue[] {
  const base: Array<Omit<MockDbIssue, 'trend' | 'competitors' | 'comments'>> = [
    { id: 'i_1001', name: '包装破损', mentions: 268, sentiment: 0.22, severity: 4 },
    { id: 'i_1002', name: '异味明显', mentions: 193, sentiment: 0.18, severity: 5 },
    { id: 'i_1003', name: '漏液', mentions: 156, sentiment: 0.28, severity: 5 },
    { id: 'i_1004', name: '口感偏差', mentions: 142, sentiment: 0.44, severity: 3 },
    { id: 'i_1005', name: '保质期疑虑', mentions: 131, sentiment: 0.36, severity: 3 },
    { id: 'i_1006', name: '配送延误', mentions: 119, sentiment: 0.48, severity: 2 },
    { id: 'i_1007', name: '外观瑕疵', mentions: 112, sentiment: 0.51, severity: 2 },
    { id: 'i_1008', name: '重量不足', mentions: 107, sentiment: 0.31, severity: 4 },
    { id: 'i_1009', name: '变形塌陷', mentions: 99, sentiment: 0.41, severity: 3 },
    { id: 'i_1010', name: '标签信息不清', mentions: 91, sentiment: 0.57, severity: 1 },
  ]

  const days = 14
  const today = new Date()
  const isoDate = (d: Date) => d.toISOString().slice(0, 10)

  return base.map((it, idx) => {
    const trend: TrendPoint[] = Array.from({ length: days }).map((_, di) => {
      const date = new Date(today.getTime() - (days - 1 - di) * 24 * 60 * 60 * 1000)
      const seed = (idx + 1) * 13 + di * 7
      const value = Math.max(0, Math.round((it.mentions / days) * (0.7 + ((seed % 17) / 100) * 1.3)))
      return { date: isoDate(date), value }
    })

    const competitors: CompetitorCompareItem[] = [
      {
        brand: '本品',
        displayName: '主商品：示例主商品',
        role: 'main',
        mentions: it.mentions,
        sentiment: it.sentiment,
      },
      {
        brand: '竞品A',
        displayName: '竞品：竞品A',
        role: 'competitor',
        mentions: Math.round(it.mentions * 0.72),
        sentiment: Math.min(0.95, it.sentiment + 0.08),
      },
      {
        brand: '竞品B',
        displayName: '竞品：竞品B',
        role: 'competitor',
        mentions: Math.round(it.mentions * 0.58),
        sentiment: Math.min(0.95, it.sentiment + 0.14),
      },
      {
        brand: '竞品C',
        displayName: '竞品：竞品C',
        role: 'competitor',
        mentions: Math.round(it.mentions * 0.64),
        sentiment: Math.min(0.95, it.sentiment + 0.03),
      },
    ]

    const comments: CommentItem[] = Array.from({ length: 43 }).map((_, ci) => {
      const createdAt = new Date(Date.now() - (ci * 2 + idx) * 60 * 60 * 1000).toISOString()
      const sentiment = Math.max(0.05, Math.min(0.95, it.sentiment + ((ci % 9) - 4) * 0.06 + 0.18))
      return {
        id: `${it.id}_c_${ci + 1}`,
        issueId: it.id,
        username: ci % 4 === 0 ? '小李' : ci % 4 === 1 ? '小周' : ci % 4 === 2 ? '匿名用户' : '小王',
        content:
          it.severity >= 4
            ? `${it.name} 这次真的比较明显，希望尽快改进。`
            : `${it.name} 偶尔会遇到，但总体还能接受。`,
        sentiment,
        createdAt,
      }
    })

    return { ...it, trend, competitors, comments }
  })
}

function seed(): MockDbData {
  return {
    users: [
      { id: 'u_admin', username: 'admin', role: 'admin', email: 'admin@local.test', status: 'active', password: 'admin123' },
      { id: 'u_demo', username: 'demo', role: 'user', email: 'demo@local.test', phone: '13800000000', status: 'active', password: 'demo123' },
    ],
    issues: seedIssues(),
  }
}

export function loadDb(): MockDbData {
  const existing = getStorageJSON<MockDbData>(STORAGE_MOCK_DB_KEY)
  if (existing && Array.isArray(existing.users) && Array.isArray(existing.issues)) return existing
  const s = seed()
  setStorageJSON(STORAGE_MOCK_DB_KEY, s)
  return s
}

export function saveDb(db: MockDbData) {
  setStorageJSON(STORAGE_MOCK_DB_KEY, db)
}

export function toTop10(issues: MockDbIssue[]): QualityIssueTopItem[] {
  return issues
    .slice()
    // 与后端保持一致：按“严重等级”降序 + 情感得分升序（越低风险越高）+ mentions 降序
    .sort((a, b) => b.severity - a.severity || a.sentiment - b.sentiment || b.mentions - a.mentions)
    .slice(0, 10)
    .map((i) => ({
      id: i.id,
      name: i.name,
      mentions: i.mentions,
      sentiment: i.sentiment,
      severity: i.severity,
    }))
}
