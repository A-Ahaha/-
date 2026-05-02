<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="page">
    <div class="card app-card">
      <div class="code">404</div>
      <div class="title">页面不存在</div>
      <div class="desc">访问路径可能已变更或输入有误。</div>
      <div class="actions">
        <el-button type="primary" @click="router.replace('/dashboard')">返回首页</el-button>
        <el-button @click="router.back()">返回上一页</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  display: grid;
  place-items: center;
  padding: 24px;
}
.card {
  width: min(540px, 94vw);
  padding: 24px;
  text-align: center;
}
.code {
  font-weight: 900;
  font-size: 56px;
  letter-spacing: 0.08em;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.92), rgba(37, 99, 235, 0.8));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.title {
  font-size: 18px;
  font-weight: 800;
  margin-top: 6px;
}
.desc {
  margin-top: 8px;
  color: var(--app-text-dim);
  font-size: 13px;
  line-height: 1.6;
}
.actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  justify-content: center;
}
</style>

