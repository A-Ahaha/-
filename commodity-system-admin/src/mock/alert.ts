import type { AlertItem, AlertStatus } from '@/types/alert'
import { delay } from '@/mock/utils'
import { mockAlerts } from '@/mock/state'

export async function mockGetAlerts(payload?: { status?: AlertStatus }): Promise<AlertItem[]> {
  await delay(320)
  const status = payload?.status
  const list = status ? mockAlerts.filter((a) => a.status === status) : mockAlerts
  return list.slice().sort((a, b) => (a.triggeredAt < b.triggeredAt ? 1 : -1))
}

export async function mockHandleAlert(payload: { id: string }): Promise<void> {
  await delay(360)
  const item = mockAlerts.find((a) => a.id === payload.id)
  if (!item) throw new Error('预警不存在')
  item.status = 'handled'
}

export async function mockGetAlertDetail(payload: { id: string }) {
  await delay(320)
  const item = mockAlerts.find((a) => a.id === payload.id)
  if (!item) throw new Error('预警不存在')
  return {
    alert: item,
    issue: {
      id: '1',
      name: item.issueName,
      mentions: 18,
      severity: 4,
      sentimentMean: 0.31,
    },
    product: {
      id: 'p_1',
      sku: 'SKU-DEMO-001',
      name: '示例商品',
      platform: 'jd',
    },
    comments: [
      {
        id: 'c_1',
        username: '用户***A',
        content: '到手第三天就出现明显问题，系统卡顿并伴随发热，影响日常使用。',
        sentiment: 0.22,
        rating: 2,
        purchaseTime: '2026-04-15T10:30:00.000Z',
        createdAt: '2026-04-17T14:33:00.000Z',
        rawProductVariant: '8+256G',
      },
      {
        id: 'c_2',
        username: '小***同学',
        content: '这个问题复现了两次，尤其是视频会议时更明显，希望尽快优化。',
        sentiment: 0.29,
        rating: 2,
        purchaseTime: '2026-04-14T08:20:00.000Z',
        createdAt: '2026-04-17T12:13:00.000Z',
        rawProductVariant: '12+256G',
      },
    ],
  }
}
