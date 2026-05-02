<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlertDetail, getAlerts, handleAlert } from '@/api/alert'
import type { AlertDetailResult, AlertItem, AlertStatus } from '@/types/alert'

const loading = ref(true)
const status = ref<AlertStatus | ''>('')
const list = ref<AlertItem[]>([])
const detailOpen = ref(false)
const detailLoading = ref(false)
const detailData = ref<AlertDetailResult | null>(null)

const filtered = computed(() => {
  if (!status.value) return list.value
  return list.value.filter((i) => i.status === status.value)
})

function fmt(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function load() {
  loading.value = true
  try {
    list.value = await getAlerts()
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

async function onHandle(row: AlertItem) {
  if (row.status === 'handled') return
  try {
    await ElMessageBox.confirm(`确认将“${row.issueName}”标记为已处理？`, '确认操作', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
    await handleAlert({ id: row.id })
    ElMessage.success('处理成功')
    await load()
  } catch {
    return
  }
}

function onView(row: AlertItem) {
  detailOpen.value = true
  detailLoading.value = true
  detailData.value = null
  getAlertDetail({ id: row.id, size: 50 })
    .then((res) => {
      detailData.value = res
    })
    .catch((e) => {
      const message = e instanceof Error ? e.message : '加载预警详情失败'
      ElMessage.error(message)
      detailOpen.value = false
    })
    .finally(() => {
      detailLoading.value = false
    })
}

onMounted(load)
</script>

<template>
  <div class="app-card">
    <div class="app-toolbar">
      <div>
        <div class="app-title">预警中心</div>
        <div class="app-subtitle">筛选、查看与处理预警事件</div>
      </div>
      <div class="tools">
        <el-select v-model="status" style="width: 160px" placeholder="状态筛选">
          <el-option label="全部" value="" />
          <el-option label="未处理" value="pending" />
          <el-option label="已处理" value="handled" />
        </el-select>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="app-section">
      <el-table v-loading="loading" :data="filtered" style="width: 100%" height="520">
        <el-table-column prop="issueName" label="问题名称" min-width="180" />
        <el-table-column prop="rule" label="触发规则" min-width="220" />
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ fmt(row.triggeredAt) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="danger" effect="dark">未处理</el-tag>
            <el-tag v-else type="success" effect="dark">已处理</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="onView(row)">详情</el-button>
            <el-button size="small" type="primary" :disabled="row.status === 'handled'" @click="onHandle(row)">
              标记已处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && filtered.length === 0" class="empty">
        <el-empty description="暂无数据" />
      </div>
    </div>
  </div>

  <el-dialog v-model="detailOpen" title="预警详情" width="980px">
    <el-skeleton :rows="6" animated :loading="detailLoading">
      <template #default>
        <div v-if="detailData" class="detail">
          <div class="meta-grid">
            <div class="meta-item">
              <div class="meta-label">问题</div>
              <div class="meta-value">{{ detailData.alert.issueName }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">规则</div>
              <div class="meta-value">{{ detailData.alert.rule }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">商品</div>
              <div class="meta-value">{{ detailData.product?.name || '—' }} / {{ detailData.product?.sku || '—' }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">触发时间</div>
              <div class="meta-value">{{ fmt(detailData.alert.triggeredAt) }}</div>
            </div>
          </div>

          <div class="section-title">导致该预警的评论（最近 {{ detailData.comments.length }} 条）</div>
          <el-table :data="detailData.comments" style="width: 100%" max-height="420">
            <el-table-column prop="username" label="用户" width="130" />
            <el-table-column prop="content" label="评论内容" min-width="420" />
            <el-table-column label="产品信息" width="200">
              <template #default="{ row }">{{ row.rawProductVariant || '—' }}</template>
            </el-table-column>
            <el-table-column label="评分" width="80" align="center">
              <template #default="{ row }">{{ row.rating ?? '—' }}</template>
            </el-table-column>
            <el-table-column label="情感分" width="90" align="center">
              <template #default="{ row }">{{ Math.round((row.sentiment || 0) * 100) }}</template>
            </el-table-column>
            <el-table-column label="购买时间" width="170">
              <template #default="{ row }">{{ row.purchaseTime ? fmt(row.purchaseTime) : '—' }}</template>
            </el-table-column>
            <el-table-column label="评论时间" width="170">
              <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-skeleton>
    <template #footer>
      <el-button @click="detailOpen = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.tools {
  display: flex;
  gap: 10px;
  align-items: center;
}
.empty {
  padding: 24px 0 4px;
}

.detail {
  display: grid;
  gap: 12px;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.meta-item {
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.76);
}

.meta-label {
  font-size: 12px;
  color: var(--app-text-dim);
}

.meta-value {
  margin-top: 6px;
  font-weight: 700;
  line-height: 1.5;
}

.section-title {
  font-weight: 700;
}
</style>
