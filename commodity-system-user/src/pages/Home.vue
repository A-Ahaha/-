<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getLatestComments, getTopIssues } from '@/api/dashboard'
import type { CommentItem, QualityIssueTopItem } from '@/types/dashboard'

const router = useRouter()
const loading = ref(true)
const topIssues = ref<QualityIssueTopItem[]>([])
const latestComments = ref<CommentItem[]>([])

const highRiskCount = computed(() => topIssues.value.filter((x) => x.severity >= 4).length)
const avgSentiment = computed(() => {
  if (!topIssues.value.length) return 0
  const total = topIssues.value.reduce((sum, item) => sum + Number(item.sentiment || 0), 0)
  return Math.round((total / topIssues.value.length) * 100)
})

function fmt(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function load() {
  loading.value = true
  try {
    const [issues, comments] = await Promise.all([getTopIssues(), getLatestComments({ size: 6 })])
    topIssues.value = issues
    latestComments.value = comments
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="grid">
    <div class="hero app-card">
      <div>
        <div class="hero-title">欢迎使用质量溯源系统</div>
        <div class="hero-sub">首页展示核心状态，深入分析请进入「数据看板」。</div>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="router.push('/dashboard')">进入数据看板</el-button>
        <el-button @click="load" :loading="loading">刷新</el-button>
      </div>
    </div>

    <div class="kpi app-card">
      <div class="kpi-label">高风险问题数</div>
      <div class="kpi-value">{{ highRiskCount }}</div>
      <div class="kpi-sub">严重度 >= 4 的问题项</div>
    </div>
    <div class="kpi app-card">
      <div class="kpi-label">问题总量</div>
      <div class="kpi-value">{{ topIssues.length }}</div>
      <div class="kpi-sub">当前已识别问题项</div>
    </div>
    <div class="kpi app-card">
      <div class="kpi-label">平均情感分</div>
      <div class="kpi-value">{{ avgSentiment }}</div>
      <div class="kpi-sub">根据问题情感均值计算</div>
    </div>

    <div class="panel app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">最近评论快照</div>
          <div class="app-subtitle">最近 6 条，点击可进入详情</div>
        </div>
        <el-button type="primary" plain size="small" @click="router.push('/comments')">全部评论</el-button>
      </div>
      <div class="app-section">
        <el-skeleton :rows="6" animated :loading="loading">
          <template #default>
            <div v-if="latestComments.length === 0" class="empty">
              <el-empty description="暂无评论数据" />
            </div>
            <div v-else class="list">
              <div v-for="c in latestComments" :key="c.id" class="item">
                <div class="meta">
                  <span>{{ c.username }}</span>
                  <span>{{ fmt(c.createdAt) }}</span>
                </div>
                <div class="text">{{ c.content }}</div>
                <el-button link type="primary" @click="router.push(`/detail/${c.issueId}`)">查看问题详情</el-button>
              </div>
            </div>
          </template>
        </el-skeleton>
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

.hero {
  grid-column: span 12;
  padding: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hero-title {
  font-size: 22px;
  font-weight: 800;
}

.hero-sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--app-text-dim);
}

.hero-actions {
  display: flex;
  gap: 10px;
}

.kpi {
  grid-column: span 4;
  padding: 16px;
}

.kpi-label {
  font-size: 12px;
  color: var(--app-text-dim);
}

.kpi-value {
  margin-top: 8px;
  font-size: 30px;
  font-weight: 900;
}

.kpi-sub {
  margin-top: 8px;
  font-size: 12px;
  color: var(--app-text-dim);
}

.panel {
  grid-column: span 12;
  overflow: hidden;
}

.list {
  display: grid;
  gap: 10px;
}

.item {
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.72);
  padding: 12px;
}

.meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--app-text-dim);
}

.text {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
}

.empty {
  padding: 22px 0 4px;
}

@media (max-width: 960px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .kpi {
    grid-column: span 12;
  }
}
</style>
