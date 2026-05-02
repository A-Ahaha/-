<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)

const formRef = ref()
const form = reactive({
  username: 'admin',
  password: 'admin123',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  if (loading.value) return
  try {
    loading.value = true
    await formRef.value?.validate?.()
    await userStore.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/admin'
    await router.replace(redirect)
  } catch (e) {
    const message = e instanceof Error ? e.message : '登录失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-backdrop" />
    <div class="auth-shell">
      <section class="auth-showcase">
        <div class="brand-line">
          <div class="brand-mark" />
          <div>
            <div class="brand-title">商品质量溯源系统</div>
            <div class="brand-sub">Quality Traceability Console</div>
          </div>
        </div>
        <h1 class="showcase-title">让评论数据成为可执行的质量改进信号</h1>
        <p class="showcase-desc">
          汇聚电商评论、自动识别问题属性与趋势波动，帮助产品与质控团队更快定位风险并闭环优化。
        </p>
        <div class="showcase-metrics">
          <div class="metric-item">
            <div class="metric-value">ABSA</div>
            <div class="metric-label">属性级情感分析</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">Trend</div>
            <div class="metric-label">问题趋势追踪</div>
          </div>
          <div class="metric-item">
            <div class="metric-value">Alert</div>
            <div class="metric-label">异常波动预警</div>
          </div>
        </div>
      </section>

      <section class="auth-card app-card">
        <div class="card-head">
          <div class="card-title">欢迎回来</div>
          <div class="card-subtitle">请输入账号密码登录管理后台</div>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" autocomplete="username" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              placeholder="请输入密码"
              type="password"
              show-password
              autocomplete="current-password"
              @keyup.enter="onSubmit"
            />
          </el-form-item>

          <el-button type="primary" :loading="loading" class="submit-btn" @click="onSubmit">
            登录系统
            <el-icon class="btn-icon">
              <ArrowRight />
            </el-icon>
          </el-button>
        </el-form>

        <div class="card-foot">
          <span>没有账号？</span>
          <router-link class="switch-link" to="/register">立即注册</router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  position: relative;
  min-height: 100%;
  display: grid;
  place-items: center;
  padding: 28px;
}

.auth-backdrop {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(900px 520px at 16% 14%, rgba(37, 99, 235, 0.18), transparent 62%),
    radial-gradient(860px 560px at 88% 18%, rgba(14, 165, 233, 0.16), transparent 62%),
    radial-gradient(920px 700px at 58% 104%, rgba(99, 102, 241, 0.1), transparent 66%);
}

.auth-shell {
  width: min(1080px, 100%);
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 24px;
  align-items: stretch;
}

.auth-showcase {
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 24px;
  padding: 28px;
  background: linear-gradient(148deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.58));
  backdrop-filter: blur(14px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
}

.brand-line {
  display: flex;
  gap: 12px;
  align-items: center;
}

.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(14, 165, 233, 0.88));
  box-shadow: 0 18px 42px rgba(30, 64, 175, 0.22);
}

.brand-title {
  font-size: 18px;
  font-weight: 800;
}

.brand-sub {
  margin-top: 2px;
  font-size: 12px;
  color: var(--app-text-dim);
}

.showcase-title {
  margin: 26px 0 0;
  max-width: 580px;
  line-height: 1.28;
  font-size: clamp(26px, 3vw, 34px);
  font-weight: 900;
  color: rgba(15, 23, 42, 0.96);
}

.showcase-desc {
  margin: 14px 0 0;
  max-width: 540px;
  line-height: 1.72;
  color: rgba(17, 24, 39, 0.66);
}

.showcase-metrics {
  margin-top: auto;
  padding-top: 24px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.metric-item {
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.66);
}

.metric-value {
  font-size: 16px;
  font-weight: 800;
}

.metric-label {
  margin-top: 5px;
  font-size: 12px;
  color: var(--app-text-dim);
}

.auth-card {
  border-radius: 24px;
  padding: 24px;
}

.card-head {
  margin-bottom: 16px;
}

.card-title {
  font-size: 24px;
  font-weight: 800;
}

.card-subtitle {
  margin-top: 4px;
  color: var(--app-text-dim);
  font-size: 13px;
}

.submit-btn {
  width: 100%;
  margin-top: 2px;
}

.btn-icon {
  margin-left: 6px;
}

.card-foot {
  margin-top: 14px;
  font-size: 13px;
  color: var(--app-text-dim);
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.switch-link {
  color: var(--app-accent);
  text-decoration: none;
  font-weight: 700;
}

.switch-link:hover {
  text-decoration: underline;
}

@media (max-width: 980px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .auth-showcase {
    padding: 22px;
  }

  .showcase-metrics {
    margin-top: 18px;
  }
}
</style>
