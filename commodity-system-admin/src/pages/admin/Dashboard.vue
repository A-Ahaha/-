<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getAlerts } from '@/api/alert'
import { getCollectJobs, getSystemConfig, getUsers } from '@/api/admin'
import type { AlertItem } from '@/types/alert'
import type { SystemConfig } from '@/types/system'
import type { UserInfo } from '@/types/user'
import type { CollectJobItem } from '@/api/admin'

const loading = ref(true)
const alerts = ref<AlertItem[]>([])
const users = ref<UserInfo[]>([])
const config = ref<SystemConfig | null>(null)
const latestCollectJob = ref<CollectJobItem | null>(null)

const pendingCount = computed(() => alerts.value.filter((a) => a.status === 'pending').length)
const collectStatusLabel = computed(() => {
  if (!config.value?.collectEnabled) return '已关闭'
  return '运行中'
})

const chartOption = computed(() => {
  const points = alerts.value
    .slice()
    .sort((a, b) => (a.triggeredAt < b.triggeredAt ? -1 : 1))
    .slice(-12)
  const x = points.map((p) => p.triggeredAt.slice(0, 10))
  const y = points.map((p) => (p.status === 'pending' ? 1 : 0))
  return {
    grid: { left: 12, right: 12, top: 24, bottom: 24, containLabel: true },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: x, axisLabel: { color: 'rgba(17,24,39,0.62)' } },
    yAxis: {
      type: 'value',
      axisLabel: { color: 'rgba(17,24,39,0.62)' },
      splitLine: { lineStyle: { color: 'rgba(17,24,39,0.08)' } },
    },
    series: [
      {
        type: 'line',
        name: '未处理预警',
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

async function load() {
  loading.value = true
  try {
    const [a, u, c, jobs] = await Promise.all([
      getAlerts(),
      getUsers(),
      getSystemConfig(),
      getCollectJobs({ page: 1, pageSize: 1 }),
    ])
    alerts.value = a
    users.value = u
    config.value = c
    latestCollectJob.value = jobs.list[0] || null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="grid">
    <div class="overview app-card">
      <div>
        <div class="overview-title">今日质量运营概览</div>
        <div class="overview-sub">关注预警处理时效、采集任务稳定性与评论情感波动，确保问题可以快速闭环。</div>
      </div>
      <el-button :loading="loading" @click="load">刷新数据</el-button>
    </div>

    <div class="kpi app-card">
      <div class="kpi-top">
        <div>
          <div class="kpi-label">未处理预警</div>
          <div class="kpi-value">{{ pendingCount }}</div>
        </div>
        <div class="kpi-badge">LIVE</div>
      </div>
      <div class="kpi-sub">需要优先处理的风险事件</div>
    </div>

    <div class="kpi app-card">
      <div class="kpi-top">
        <div>
          <div class="kpi-label">系统用户数</div>
          <div class="kpi-value">{{ users.length }}</div>
        </div>
        <div class="kpi-badge kpi-badge-2">IAM</div>
      </div>
      <div class="kpi-sub">账号/角色/状态统一管理</div>
    </div>

    <div class="kpi app-card">
      <div class="kpi-top">
        <div>
          <div class="kpi-label">预警阈值</div>
          <div class="kpi-value">{{ config?.alertThreshold ?? '—' }}</div>
        </div>
        <div class="kpi-badge kpi-badge-3">RULE</div>
      </div>
      <div class="kpi-sub">阈值越低，预警更敏感</div>
    </div>

    <div class="kpi app-card">
      <div class="kpi-top">
        <div>
          <div class="kpi-label">定时采集</div>
          <div class="kpi-value">{{ collectStatusLabel }}</div>
        </div>
        <div class="kpi-badge kpi-badge-2">CRON</div>
      </div>
      <div class="kpi-sub">
        {{ config?.collectSku || '未配置 SKU' }} / {{ config?.collectFrequencyMinutes ?? '—' }} 分钟
      </div>
    </div>

    <div class="panel app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">预警触发趋势</div>
          <div class="app-subtitle">近 12 条触发记录</div>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
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
          <div class="app-title">最近采集任务</div>
          <div class="app-subtitle">展示自动采集最近一次执行状态</div>
        </div>
      </div>
      <div class="app-section">
        <div class="split" v-if="latestCollectJob">
          <div class="split-item">
            <div class="split-label">任务状态</div>
            <div class="split-val">{{ latestCollectJob.status }}</div>
          </div>
          <div class="split-item">
            <div class="split-label">导入 / 采集</div>
            <div class="split-val">{{ latestCollectJob.totalImported }} / {{ latestCollectJob.totalCollected }}</div>
          </div>
        </div>
        <div v-else class="split">
          <div class="split-item">
            <div class="split-label">最近采集任务</div>
            <div class="split-val">—</div>
          </div>
          <div class="split-item">
            <div class="split-label">说明</div>
            <div class="split-val">暂无记录</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 14px;
}

.overview {
  grid-column: span 12;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background:
    radial-gradient(520px 220px at 6% 10%, rgba(37, 99, 235, 0.1), transparent 65%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(255, 255, 255, 0.74));
}

.overview-title {
  font-size: 18px;
  font-weight: 800;
}

.overview-sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--app-text-dim);
}

.kpi {
  grid-column: span 4;
  padding: 16px;
}

.kpi-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.kpi-label {
  font-size: 12px;
  color: var(--app-text-dim);
}

.kpi-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 900;
  letter-spacing: 0.02em;
}

.kpi-sub {
  margin-top: 10px;
  font-size: 12px;
  color: var(--app-text-dim);
}

.kpi-badge {
  font-size: 12px;
  font-weight: 800;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  background: rgba(37, 99, 235, 0.06);
  color: rgba(37, 99, 235, 0.92);
}

.kpi-badge-2 {
  border-color: rgba(6, 182, 212, 0.18);
  background: rgba(6, 182, 212, 0.06);
  color: rgba(6, 182, 212, 0.92);
}

.kpi-badge-3 {
  border-color: rgba(239, 68, 68, 0.18);
  background: rgba(239, 68, 68, 0.06);
  color: rgba(239, 68, 68, 0.92);
}

.panel {
  grid-column: span 8;
  overflow: hidden;
}

.panel:last-child {
  grid-column: span 4;
}

.chart {
  height: 280px;
}

.split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.split-item {
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.75);
}

.split-label {
  color: var(--app-text-dim);
  font-size: 12px;
}

.split-val {
  margin-top: 10px;
  font-size: 22px;
  font-weight: 900;
}

@media (max-width: 960px) {
  .overview {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .kpi {
    grid-column: span 12;
  }

  .panel,
  .panel:last-child {
    grid-column: span 12;
  }
}
</style>
