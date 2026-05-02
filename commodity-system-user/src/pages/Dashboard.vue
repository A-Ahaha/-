<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getLatestComments, getTopIssues, getTrendData } from '@/api/dashboard'
import { analyzeProduct, type ProductAbsaResult } from '@/api/product'
import type { CommentItem, QualityIssueTopItem, TrendPoint } from '@/types/dashboard'

const router = useRouter()

const loading = ref(true)
const topIssues = ref<QualityIssueTopItem[]>([])
const trend = ref<TrendPoint[]>([])
const comments = ref<CommentItem[]>([])

const absaVisible = ref(false)
const absaLoading = ref(false)
const absaResult = ref<ProductAbsaResult | null>(null)

function severityLabel(v: number) {
  return v >= 5 ? '极高' : v >= 4 ? '高' : v >= 3 ? '中' : v >= 2 ? '低' : '提示'
}

function severityType(v: number) {
  return v >= 5 ? 'danger' : v >= 4 ? 'warning' : v >= 3 ? 'info' : 'success'
}

function fmt(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const chartOption = computed(() => ({
  grid: { left: 12, right: 12, top: 24, bottom: 24, containLabel: true },
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: trend.value.map((p) => p.date.slice(5)), axisLabel: { color: 'rgba(17,24,39,0.62)' } },
  yAxis: {
    type: 'value',
    axisLabel: { color: 'rgba(17,24,39,0.62)' },
    splitLine: { lineStyle: { color: 'rgba(17,24,39,0.08)' } },
  },
  series: [
    {
      type: 'line',
      name: '情感趋势',
      data: trend.value.map((p) => p.value),
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      lineStyle: { width: 3, color: 'rgba(37,99,235,0.92)' },
      itemStyle: { color: 'rgba(37,99,235,0.92)' },
      areaStyle: { color: 'rgba(37,99,235,0.12)' },
    },
  ],
}))

async function load() {
  loading.value = true
  try {
    const [top, t, c] = await Promise.all([getTopIssues(), getTrendData({ days: 14 }), getLatestComments({ size: 12 })])
    topIssues.value = top
    trend.value = t
    comments.value = c
  } finally {
    loading.value = false
  }
}

async function runAbsaDemo() {
  absaLoading.value = true
  try {
    // 默认分析当前主商品（ID=1 可按需替换）
    const res = await analyzeProduct({ id: 1 })
    absaResult.value = res
    absaVisible.value = true
  } catch (e) {
    ElMessage.error('分析失败，请稍后重试')
  } finally {
    absaLoading.value = false
  }
}

function goDetail(id: string) {
  router.push(`/detail/${id}`)
}

function onIssueRowClick(row: QualityIssueTopItem) {
  goDetail(row.id)
}

onMounted(load)
</script>

<template>
  <div class="grid">
    <div class="panel app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">质量问题排行榜</div>
          <div class="app-subtitle">Top10 · 点击查看详情</div>
        </div>
        <div class="toolbar-actions">
          <el-button :loading="loading" @click="load">刷新</el-button>
          <el-button type="primary" plain size="small" :loading="absaLoading" @click="runAbsaDemo">
            商品 ABSA 分析
          </el-button>
        </div>
      </div>
      <div class="app-section">
        <el-skeleton :rows="8" animated :loading="loading">
          <template #default>
            <el-table :data="topIssues" style="width: 100%" height="420" @row-click="onIssueRowClick">
              <el-table-column prop="name" label="问题" min-width="170" />
              <el-table-column prop="mentions" label="提及次数" width="120" align="right" />
              <el-table-column label="情感强度" width="140" align="center">
                <template #default="{ row }">
                  <el-progress :percentage="Math.round(row.sentiment * 100)" :stroke-width="10" />
                </template>
              </el-table-column>
              <el-table-column label="严重等级" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="severityType(row.severity)" effect="dark">{{ severityLabel(row.severity) }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-skeleton>
      </div>
    </div>

    <div class="panel app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">情感趋势</div>
          <div class="app-subtitle">近 14 天</div>
        </div>
      </div>
      <div class="app-section">
        <el-skeleton :rows="6" animated :loading="loading">
          <template #default>
            <VChart class="chart" :option="chartOption" autoresize />
          </template>
        </el-skeleton>
      </div>
    </div>

    <div class="panel app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">最新评论</div>
          <div class="app-subtitle">点击进入对应问题详情</div>
        </div>
      </div>
      <div class="app-section">
        <el-skeleton :rows="8" animated :loading="loading">
          <template #default>
            <div v-if="comments.length === 0" class="empty">
              <el-empty description="暂无数据" />
            </div>
            <div v-else class="list">
              <div v-for="c in comments" :key="c.id" class="item app-card">
                <div class="item-top">
                  <div class="user">{{ c.username }}</div>
                  <div class="time">{{ fmt(c.createdAt) }}</div>
                </div>
                <div class="content">{{ c.content }}</div>
                <div class="bottom">
                  <div class="pill">情感：{{ Math.round(c.sentiment * 100) }}</div>
                  <el-button size="small" type="primary" plain @click="router.push(`/detail/${c.issueId}`)">查看</el-button>
                </div>
              </div>
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>
  </div>

  <el-dialog v-model="absaVisible" title="示例商品 ABSA 分析" width="540px">
    <div v-if="!absaResult">正在分析...</div>
    <div v-else>
      <div class="absa-title">{{ absaResult.product_name }}</div>
      <el-table :data="absaResult.aspects" size="small" style="width: 100%">
        <el-table-column prop="aspect" label="属性" min-width="160" />
        <el-table-column prop="sentiment" label="情感倾向" width="120" />
        <el-table-column label="置信度" width="160" align="center">
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.confidence * 100)" :stroke-width="8" />
          </template>
        </el-table-column>
      </el-table>
      <div class="absa-tip">
        数据来自已导入的真实评论 CSV，并按 ABSA 规则自动抽取属性情感对。
      </div>
    </div>
    <template #footer>
      <el-button @click="absaVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 14px;
}

.panel {
  grid-column: span 8;
  overflow: hidden;
}

.panel:nth-child(2) {
  grid-column: span 4;
}

.panel:nth-child(3) {
  grid-column: span 12;
}

.chart {
  height: 280px;
}

.list {
  display: grid;
  gap: 10px;
}

.item {
  padding: 12px;
  box-shadow: none;
  background: rgba(255, 255, 255, 0.75);
}

.item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user {
  font-weight: 900;
}

.time {
  font-size: 12px;
  color: var(--app-text-dim);
}

.content {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(17, 24, 39, 0.8);
}

.bottom {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pill {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  background: rgba(255, 255, 255, 0.9);
  color: rgba(17, 24, 39, 0.68);
}

.empty {
  padding: 24px 0 4px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.absa-title {
  margin-bottom: 12px;
  font-weight: 600;
}

.absa-tip {
  margin-top: 10px;
  font-size: 12px;
  color: var(--app-text-dim);
}

@media (max-width: 980px) {
  .panel,
  .panel:nth-child(2),
  .panel:nth-child(3) {
    grid-column: span 12;
  }
}
</style>
