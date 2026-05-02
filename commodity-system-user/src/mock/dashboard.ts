import type { CommentItem, TrendPoint } from '@/types/dashboard'
import { delay } from '@/mock/utils'
import { loadDb, toTop10 } from '@/mock/db'

export async function mockGetTopIssues() {
  await delay(320)
  const db = loadDb()
  return toTop10(db.issues)
}

export async function mockGetTrendData(payload?: { days?: number }): Promise<TrendPoint[]> {
  await delay(340)
  const db = loadDb()
  const days = Math.max(7, Math.min(30, Math.floor(payload?.days ?? 14)))
  const merged: Record<string, number> = {}
  for (const issue of db.issues.slice(0, 6)) {
    for (const p of issue.trend.slice(-days)) {
      merged[p.date] = (merged[p.date] ?? 0) + p.value
    }
  }
  return Object.keys(merged)
    .sort()
    .map((date) => ({ date, value: merged[date] }))
}

export async function mockGetLatestComments(payload?: { size?: number }): Promise<CommentItem[]> {
  await delay(320)
  const db = loadDb()
  const size = Math.max(5, Math.min(30, Math.floor(payload?.size ?? 12)))
  const all = db.issues.flatMap((i) => i.comments.map((c) => ({ ...c, id: `${i.id}_${c.id}`, issueId: i.id })))
  return all.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1)).slice(0, size)
}
