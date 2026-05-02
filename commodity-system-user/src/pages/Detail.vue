<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getBatchTrend, getComments, getDetailById } from '@/api/detail'
import type { BatchTrendResponse, IssueDetail, PagedComments } from '@/types/detail'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const detail = ref<IssueDetail | null>(null)
const batchTrend = ref<BatchTrendResponse | null>(null)
const commentLoading = ref(true)
const commentPage = ref(1)
const commentPageSize = ref(8)
const commentTotal = ref(0)
const comments = ref<PagedComments['list']>([])
const competitorDisplayMode = ref<'all' | 'withIssue'>('all')

const id = computed(() => String(route.params.id || ''))

function severityLabel(v: number) {
  return v >= 5 ? '极高' : v >= 4 ? '高' : v >= 3 ? '中' : v >= 2 ? '低' : '提示'
}

function severityType(v: number) {
  return v >= 5 ? 'danger' : v >= 4 ? 'warning' : v >= 3 ? 'info' : 'success'
}

function fmt(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const trendOption = computed(() => {
  const d = detail.value
  const x = d?.trend.map((p) => p.date.slice(5)) ?? []
  const y = d?.trend.map((p) => p.value) ?? []
  return {
    grid: { left: 12, right: 12, top: 24, bottom: 24, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: x, axisLabel: { color: 'rgba(17,24,39,0.62)' } },
    yAxis: { type: 'value', axisLabel: { color: 'rgba(17,24,39,0.62)' }, splitLine: { lineStyle: { color: 'rgba(17,24,39,0.08)' } } },
    series: [
      {
        type: 'line',
        data: y,
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 3, color: 'rgba(37,99,235,0.92)' },
        itemStyle: { color: 'rgba(37,99,235,0.92)' },
        areaStyle: { color: 'rgba(37,99,235,0.12)' },
      },
    ],
  }
})

const hasCompetitorIssue = computed(() => {
  const rows = detail.value?.competitors || []
  return rows.some((c) => c.role === 'competitor' && Number(c.mentions || 0) > 0)
})

const competitorRowsBase = computed(() => {
  const rows = (detail.value?.competitors || []).slice()
  if (competitorDisplayMode.value === 'withIssue') {
    const mainRows = rows.filter((c) => c.role === 'main')
    const competitorRows = rows.filter((c) => c.role === 'competitor' && Number(c.mentions || 0) > 0)
    return [...mainRows, ...competitorRows]
  }
  return rows
})

const competitorRowsForView = computed(() => {
  const rows = competitorRowsBase.value.slice()
  if (!rows.length) return rows
  if (competitorDisplayMode.value === 'all' && !hasCompetitorIssue.value) {
    rows.push({
      brand: '暂无竞品问题',
      displayName: '竞品：暂无同类问题',
      role: 'competitor',
      mentions: 0,
      sentiment: 1,
    })
  }
  return rows
})

const competitorOption = computed(() => {
  const competitors = competitorRowsForView.value
  const x = competitors.map((c) => (c.role === 'main' ? '主商品' : c.brand.replace(/^竞品[:：]?/, '') || '竞品'))
  const maxMentions = Math.max(1, ...competitors.map((c) => Number(c.mentions || 0)))
  // 归一化提及占比（0-100），避免提及量绝对值过大时掩盖另一条指标
  const mentionsShare = competitors.map((c) => Math.round((Number(c.mentions || 0) / maxMentions) * 100))
  // 风险强度：情感越低，风险越高
  const riskIntensity = competitors.map((c) => Math.round((1 - Number(c.sentiment || 0)) * 100))
  const barColors = competitors.map((c) =>
    c.role === 'main' ? 'rgba(37,99,235,0.92)' : 'rgba(6,182,212,0.85)',
  )

  return {
    grid: { left: 12, right: 12, top: 54, bottom: 44, containLabel: true },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const idx = params?.[0]?.dataIndex ?? 0
        const item = competitors[idx]
        const mentionPct = mentionsShare[idx] ?? 0
        const riskPct = riskIntensity[idx] ?? 0
        return [
          `${item?.displayName || item?.brand || '-'}`,
          `问题提及占比：${mentionPct}%`,
          `问题风险强度：${riskPct}%`,
          `提及次数：${item?.mentions ?? 0}`,
        ].join('<br/>')
      },
    },
    legend: { data: ['问题提及占比', '问题风险强度'] },
    xAxis: {
      type: 'category',
      data: x,
      axisLabel: { color: 'rgba(17,24,39,0.62)', interval: 0, rotate: 0, margin: 10 },
    },
    yAxis: [{ type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: 'rgba(17,24,39,0.08)' } } }],
    series: [
      {
        type: 'bar',
        name: '问题提及占比',
        data: mentionsShare,
        barWidth: 26,
        itemStyle: {
          color: (params: { dataIndex: number }) => barColors[params.dataIndex] || 'rgba(6,182,212,0.85)',
          borderRadius: [8, 8, 0, 0],
        },
      },
      {
        type: 'line',
        name: '问题风险强度',
        data: riskIntensity,
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3, color: 'rgba(239,68,68,0.9)' },
        itemStyle: { color: 'rgba(239,68,68,0.9)' },
      },
    ],
  }
})

const batchTrendOption = computed(() => {
  const bt = batchTrend.value
  const x = bt?.date.map((d) => d.slice(5)) ?? []
  const series = (bt?.batches ?? []).map((b, idx) => ({
    type: 'line',
    name: b.batchName,
    data: b.series,
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 3 },
    // 让每条线颜色更稳定一些
    color: ['rgba(37,99,235,0.92)', 'rgba(6,182,212,0.85)', 'rgba(245,158,11,0.92)', 'rgba(239,68,68,0.9)'][idx % 4],
  }))

  return {
    grid: { left: 12, right: 12, top: 24, bottom: 24, containLabel: true },
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    xAxis: { type: 'category', data: x, axisLabel: { color: 'rgba(17,24,39,0.62)' } },
    yAxis: { type: 'value', axisLabel: { color: 'rgba(17,24,39,0.62)' }, splitLine: { lineStyle: { color: 'rgba(17,24,39,0.08)' } } },
    series,
  }
})

async function loadDetail() {
  loading.value = true
  try {
    detail.value = await getDetailById({ id: id.value })
    batchTrend.value = await getBatchTrend({ id: id.value })
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

async function loadComments() {
  commentLoading.value = true
  try {
    const res = await getComments({ id: id.value, page: commentPage.value, pageSize: commentPageSize.value })
    comments.value = res.list
    commentTotal.value = res.total
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(message)
  } finally {
    commentLoading.value = false
  }
}

function onPageChange(p: number) {
  commentPage.value = p
  loadComments()
}

function onPageSizeChange(s: number) {
  commentPageSize.value = s
  commentPage.value = 1
  loadComments()
}

watch(
  () => id.value,
  async () => {
    commentPage.value = 1
    await Promise.all([loadDetail(), loadComments()])
  },
)

onMounted(async () => {
  await Promise.all([loadDetail(), loadComments()])
})
</script>

<template>
  <div class="grid">
    <div class="panel app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">详情查询</div>
          <div class="app-subtitle">质量问题分析与溯源</div>
        </div>
        <div class="tools">
          <el-button @click="router.back()">返回</el-button>
          <el-button :loading="loading" @click="loadDetail">刷新</el-button>
        </div>
      </div>

      <div class="app-section">
        <el-skeleton :rows="7" animated :loading="loading">
          <template #default>
            <div class="head">
              <div>
                <div class="name">{{ detail?.name || '—' }}</div>
                <div class="meta">主商品：{{ detail?.productName || '—' }} ｜ 问题ID：{{ detail?.id || '—' }}</div>
              </div>
              <div class="tags">
                <el-tag v-if="detail" :type="severityType(detail.severity)" effect="dark">{{ severityLabel(detail.severity) }}</el-tag>
                <div class="pill">提及：{{ detail?.mentions ?? '—' }}</div>
                <div class="pill">情感：{{ detail ? Math.round(detail.sentiment * 100) : '—' }}</div>
              </div>
            </div>

            <div class="charts">
              <div class="chart-card app-card">
                <div class="chart-title">趋势图</div>
                <VChart class="chart" :option="trendOption" autoresize />
              </div>
              <div class="chart-card app-card">
                <div class="chart-head">
                  <div class="chart-title">主商品 vs 竞品对比（问题提及占比 / 风险强度）</div>
                  <el-radio-group v-model="competitorDisplayMode" size="small">
                    <el-radio-button label="all">显示全部竞品</el-radio-button>
                    <el-radio-button label="withIssue">仅显示有该问题竞品</el-radio-button>
                  </el-radio-group>
                </div>
                <VChart class="chart" :option="competitorOption" autoresize />
                <div class="chart-tip">
                  蓝色柱：主商品，青色柱：竞品；红线越高表示该质量问题在对应商品上风险越高。
                </div>
                <el-alert
                  v-if="competitorDisplayMode === 'all' && !hasCompetitorIssue"
                  style="margin-top: 10px"
                  type="info"
                  :closable="false"
                  title="当前竞品数据中暂未检索到该质量问题，图表已按“主商品 vs 竞品暂无问题(0)”展示。"
                />
                <el-alert
                  v-if="competitorDisplayMode === 'withIssue' && competitorRowsForView.filter((x) => x.role === 'competitor').length === 0"
                  style="margin-top: 10px"
                  type="warning"
                  :closable="false"
                  title="当前筛选条件下暂无“有该问题”的竞品，已仅展示主商品。可切换为“显示全部竞品”查看0值基线。"
                />
                <el-table :data="competitorRowsForView" size="small" style="margin-top: 10px; width: 100%">
                  <el-table-column label="商品" min-width="220">
                    <template #default="{ row }">
                      {{ row.displayName || row.brand }}
                    </template>
                  </el-table-column>
                  <el-table-column label="角色" width="100" align="center">
                    <template #default="{ row }">
                      <el-tag :type="row.role === 'main' ? 'primary' : 'info'" effect="light">
                        {{ row.role === 'main' ? '主商品' : '竞品' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="mentions" label="提及次数" width="110" align="right" />
                  <el-table-column label="情感得分" width="110" align="center">
                    <template #default="{ row }">{{ Math.round((row.sentiment || 0) * 100) }}%</template>
                  </el-table-column>
                  <el-table-column label="风险强度" width="110" align="center">
                    <template #default="{ row }">{{ Math.round((1 - (row.sentiment || 0)) * 100) }}%</template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="chart-card app-card">
                <div class="chart-title">批次提及趋势（近 14 天）</div>
                <VChart class="chart" :option="batchTrendOption" autoresize />
              </div>
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>

    <div class="panel app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">评论列表</div>
          <div class="app-subtitle">支持分页</div>
        </div>
      </div>

      <div class="app-section">
        <el-table v-loading="commentLoading" :data="comments" style="width: 100%" height="420">
          <el-table-column prop="username" label="用户" width="120" />
          <el-table-column prop="content" label="内容" min-width="260" />
          <el-table-column label="情感" width="110" align="center">
            <template #default="{ row }">{{ Math.round(row.sentiment * 100) }}</template>
          </el-table-column>
          <el-table-column label="时间" width="170">
            <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
          </el-table-column>
        </el-table>

        <div class="pager">
          <el-pagination
            :current-page="commentPage"
            :page-size="commentPageSize"
            :total="commentTotal"
            layout="total, sizes, prev, pager, next"
            :page-sizes="[8, 12, 20]"
            @update:current-page="onPageChange"
            @update:page-size="onPageSizeChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.tools {
  display: flex;
  gap: 10px;
  align-items: center;
}

.head {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  justify-content: space-between;
}

.name {
  font-weight: 900;
  font-size: 18px;
}

.meta {
  margin-top: 4px;
  font-size: 12px;
  color: var(--app-text-dim);
}

.tags {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.pill {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  background: rgba(255, 255, 255, 0.9);
  color: rgba(17, 24, 39, 0.68);
}

.charts {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.chart-card {
  padding: 12px;
  box-shadow: none;
  background: rgba(255, 255, 255, 0.75);
}

.chart-title {
  font-weight: 900;
}

.chart-head {
  margin-bottom: 8px;
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
}

.chart {
  height: 260px;
}

.chart-tip {
  margin-top: 6px;
  font-size: 12px;
  color: var(--app-text-dim);
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}

@media (max-width: 980px) {
  .charts {
    grid-template-columns: 1fr;
  }

  .chart-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

