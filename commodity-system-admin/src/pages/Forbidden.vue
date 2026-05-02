<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="page">
    <div class="card app-card">
      <div class="code">403</div>
      <div class="title">无访问权限</div>
      <div class="desc">当前账号无权访问该页面，请联系管理员或切换账号。</div>
      <div class="actions">
        <el-button type="primary" @click="router.replace('/admin')">返回概览</el-button>
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
  background: linear-gradient(135deg, rgba(51, 214, 255, 0.95), rgba(255, 77, 109, 0.7));
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
