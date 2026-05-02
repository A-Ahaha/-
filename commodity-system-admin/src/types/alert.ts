export type AlertStatus = 'pending' | 'handled'

export interface AlertItem {
  id: string
  issueName: string
  rule: string
  triggeredAt: string
  status: AlertStatus
}

export interface AlertDetailCommentItem {
  id: string
  username: string
  content: string
  sentiment: number
  rating: number | null
  purchaseTime: string
  createdAt: string
  rawProductVariant: string
}

export interface AlertDetailResult {
  alert: AlertItem
  issue: {
    id: string
    name: string
    mentions: number
    severity: number
    sentimentMean: number
  } | null
  product: {
    id: string
    sku: string
    name: string
    platform: string
  } | null
  comments: AlertDetailCommentItem[]
}
