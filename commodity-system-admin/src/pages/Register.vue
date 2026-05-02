<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, User } from '@element-plus/icons-vue'
import { register as registerApi } from '@/api/auth'

const router = useRouter()
const loading = ref(false)
const formRef = ref()
const form = reactive({
  username: '',
  phone: '',
  password: '',
  confirmPassword: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule: unknown, value: string, callback: (err?: Error) => void) => {
        if (value !== form.password) return callback(new Error('两次输入的密码不一致'))
        callback()
      },
      trigger: 'blur',
    },
  ],
}

async function onSubmit() {
  if (loading.value) return
  try {
    loading.value = true
    await formRef.value?.validate?.()
    await registerApi({
      username: form.username.trim(),
      password: form.password,
      phone: form.phone.trim() || undefined,
    })
    ElMessage.success('注册成功，请登录')
    await router.replace('/login')
  } catch (e) {
    const message = e instanceof Error ? e.message : '注册失败'
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
        <h1 class="showcase-title">创建你的工作账号，开始搭建质量监控闭环</h1>
        <ul class="showcase-list">
          <li><el-icon><Check /></el-icon>评论导入后自动聚合问题属性与严重度</li>
          <li><el-icon><Check /></el-icon>支持主商品与竞品的质量对比分析</li>
          <li><el-icon><Check /></el-icon>支持阈值预警与定时采集任务跟踪</li>
        </ul>
      </section>

      <section class="auth-card app-card">
        <div class="card-head">
          <div class="card-title">账号注册</div>
          <div class="card-subtitle">填写信息后即可创建普通用户账号</div>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" autocomplete="username">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="手机号（可选）" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" autocomplete="new-password" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              show-password
              placeholder="请再次输入密码"
              autocomplete="new-password"
              @keyup.enter="onSubmit"
            />
          </el-form-item>

          <el-button type="primary" :loading="loading" class="submit-btn" @click="onSubmit">创建账号</el-button>
        </el-form>

        <div class="card-foot">
          <span>已有账号？</span>
          <router-link class="switch-link" to="/login">返回登录</router-link>
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
  line-height: 1.3;
  font-size: clamp(24px, 2.8vw, 32px);
  font-weight: 900;
  color: rgba(15, 23, 42, 0.96);
}

.showcase-list {
  margin: 18px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.showcase-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(17, 24, 39, 0.72);
}

.showcase-list .el-icon {
  color: var(--app-accent);
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
}
</style>
