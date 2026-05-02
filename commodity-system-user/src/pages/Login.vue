<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getAdminAppUrl } from '@/api/env'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const formRef = ref()
const form = reactive({
  username: 'demo',
  password: 'demo123',
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

    if (userStore.role === 'admin') {
      const adminUrl = getAdminAppUrl()
      if (adminUrl) {
        const base = adminUrl.endsWith('/') ? adminUrl.slice(0, -1) : adminUrl
        window.location.href = `${base}/admin`
        return
      }
      ElMessage.warning('当前账号为管理员，请打开管理端应用')
      return
    }

    ElMessage.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/home'
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
  <div class="login">
    <div class="login-bg" />
    <div class="login-card app-card">
      <div class="login-head">
        <div class="login-brand">
          <div class="login-mark" />
          <div>
            <div class="login-title">商品质量溯源系统</div>
            <div class="login-sub">用户端 · 登录</div>
          </div>
        </div>
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

        <el-button type="primary" :loading="loading" style="width: 100%" @click="onSubmit">登录</el-button>
        <div class="login-actions">
          <span class="muted">没有账号？</span>
          <el-button link type="primary" @click="router.push('/register')">去注册</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login {
  position: relative;
  height: 100%;
  display: grid;
  place-items: center;
  padding: 24px;
}

.login-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(980px 620px at 25% 18%, rgba(37, 99, 235, 0.16), transparent 60%),
    radial-gradient(900px 620px at 82% 22%, rgba(6, 182, 212, 0.14), transparent 60%),
    radial-gradient(900px 700px at 60% 110%, rgba(99, 102, 241, 0.08), transparent 62%);
  pointer-events: none;
}

.login-card {
  width: min(460px, 92vw);
  padding: 18px 18px 20px;
  position: relative;
  z-index: 1;
}

.login-head {
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
}

.login-brand {
  display: flex;
  gap: 12px;
  align-items: center;
}

.login-mark {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.92), rgba(6, 182, 212, 0.86));
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
}

.login-title {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.login-sub {
  font-size: 12px;
  color: var(--app-text-dim);
}

.login-actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.muted {
  font-size: 12px;
  color: var(--app-text-dim);
}
</style>
