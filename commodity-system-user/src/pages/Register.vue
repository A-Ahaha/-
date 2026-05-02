<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '@/api/auth'

const router = useRouter()

const loading = ref(false)
const formRef = ref()
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  phone: '',
})

function isPhone(v: string) {
  if (!v) return true
  return /^1[3-9]\d{9}$/.test(v)
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
        if (value !== form.password) cb(new Error('两次密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
  phone: [
    {
      validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
        if (!isPhone(value)) cb(new Error('手机号格式不正确'))
        else cb()
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
    await register({ username: form.username, password: form.password, phone: form.phone || undefined })
    ElMessage.success('注册成功')
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
  <div class="page">
    <div class="card app-card">
      <div class="head">
        <div>
          <div class="title">创建账号</div>
          <div class="sub">普通用户注册（Mock）</div>
        </div>
        <el-button link type="primary" @click="router.push('/login')">返回登录</el-button>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="必填" autocomplete="username" />
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
        <el-form-item label="手机号（可选）" prop="phone">
          <el-input v-model="form.phone" placeholder="11 位手机号" autocomplete="tel" />
        </el-form-item>

        <el-button type="primary" :loading="loading" style="width: 100%" @click="onSubmit">注册</el-button>
      </el-form>
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
  width: min(480px, 92vw);
  padding: 18px 18px 20px;
}

.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.title {
  font-size: 18px;
  font-weight: 900;
}

.sub {
  margin-top: 2px;
  font-size: 12px;
  color: var(--app-text-dim);
}
</style>

