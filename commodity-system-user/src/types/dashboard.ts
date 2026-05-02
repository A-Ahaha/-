export interface QualityIssueTopItem {
  id: string
  name: string
  mentions: number
  sentiment: number
  severity: 1 | 2 | 3 | 4 | 5
}

export interface TrendPoint {
  date: string
  value: number
}

export interface CommentItem {
  id: string
  issueId: string
  username: string
  content: string
  sentiment: number
  createdAt: string
}

export interface PagedCommentResult {
  list: CommentItem[]
  total: number
}
