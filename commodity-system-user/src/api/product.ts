import { request } from '@/utils/request'
import { useMockApi } from '@/api/env'

export interface AbsaAspect {
  aspect: string
  sentiment: 'positive' | 'neutral' | 'negative' | string
  confidence: number
}

export interface ProductAbsaResult {
  product_name: string
  aspects: AbsaAspect[]
}

export async function analyzeProduct(payload: { id: number | string }): Promise<ProductAbsaResult> {
  // 开发环境如果仍然使用 Mock，则给出一个固定的演示结构
  if (useMockApi()) {
    return {
      product_name: '示例商品（Mock）',
      aspects: [
        { aspect: '电池续航', sentiment: 'negative', confidence: 0.86 },
        { aspect: '屏幕', sentiment: 'neutral', confidence: 0.74 },
        { aspect: '发热', sentiment: 'negative', confidence: 0.81 },
      ],
    }
  }
  return request({
    url: `/user/products/${payload.id}`,
    method: 'GET',
  })
}

