<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="page">
    <div class="card app-card">
      <div class="code">403</div>
      <div class="title">无访问权限</div>
      <div class="desc">当前账号无权访问该页面，请切换账号。</div>
      <div class="actions">
        <el-button type="primary" @click="router.replace('/dashboard')">返回首页</el-button>
        <el-button @click="router.replace('/login')">去登录</el-button>
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
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(239, 68, 68, 0.76));
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

