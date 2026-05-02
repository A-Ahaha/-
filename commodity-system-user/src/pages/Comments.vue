<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAllComments } from '@/api/dashboard'
import type { CommentItem } from '@/types/dashboard'

const router = useRouter()
const loading = ref(true)
const list = ref<CommentItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

function fmt(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function load() {
  loading.value = true
  try {
    const res = await getAllComments({ page: page.value, pageSize: pageSize.value })
    list.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  load()
}

function onPageSizeChange(s: number) {
  pageSize.value = s
  page.value = 1
  load()
}

onMounted(load)
</script>

<template>
  <div class="app-card">
    <div class="app-toolbar">
      <div>
        <div class="app-title">全部评论</div>
        <div class="app-subtitle">当前商品的完整评论列表（按时间倒序）</div>
      </div>
      <div class="actions">
        <el-button @click="router.push('/home')">返回首页</el-button>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <div class="app-section">
      <el-table v-loading="loading" :data="list" style="width: 100%" height="560">
        <el-table-column prop="username" label="用户" width="130" />
        <el-table-column prop="content" label="评论内容" min-width="420" />
        <el-table-column label="情感分" width="100" align="center">
          <template #default="{ row }">{{ Math.round(row.sentiment * 100) }}</template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 30, 50]"
          layout="total, sizes, prev, pager, next"
          @update:current-page="onPageChange"
          @update:page-size="onPageSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.actions {
  display: flex;
  gap: 10px;
}

.pager {
  padding-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
