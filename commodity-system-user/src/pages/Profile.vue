<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const info = computed(() => userStore.userInfo)

async function onLogout() {
  try {
    await ElMessageBox.confirm('确认退出登录？', '提示', {
      type: 'warning',
      confirmButtonText: '退出',
      cancelButtonText: '取消',
    })
    userStore.logout()
    ElMessage.success('已退出')
    await router.replace('/login')
  } catch {
    return
  }
}
</script>

<template>
  <div class="app-card">
    <div class="app-toolbar">
      <div>
        <div class="app-title">个人中心</div>
        <div class="app-subtitle">当前登录账号信息</div>
      </div>
      <el-button type="danger" plain @click="onLogout">退出登录</el-button>
    </div>

    <div class="app-section">
      <div class="profile">
        <div class="avatar">
          <div class="ring" />
          <div class="name">{{ info?.username?.slice(0, 1)?.toUpperCase() || 'U' }}</div>
        </div>

        <div class="meta">
          <div class="row">
            <div class="k">用户名</div>
            <div class="v">{{ info?.username || '—' }}</div>
          </div>
          <div class="row">
            <div class="k">角色</div>
            <div class="v">{{ info?.role || '—' }}</div>
          </div>
          <div class="row">
            <div class="k">邮箱</div>
            <div class="v">{{ info?.email || '—' }}</div>
          </div>
          <div class="row">
            <div class="k">手机号</div>
            <div class="v">{{ info?.phone || '—' }}</div>
          </div>
          <div class="row">
            <div class="k">状态</div>
            <div class="v">{{ info?.status || '—' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 18px;
  align-items: start;
}

.avatar {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 26px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(17, 24, 39, 0.12);
  overflow: hidden;
}

.ring {
  position: absolute;
  inset: -22px;
  background: conic-gradient(
    from 180deg,
    rgba(37, 99, 235, 0.9),
    rgba(6, 182, 212, 0.86),
    rgba(99, 102, 241, 0.78),
    rgba(37, 99, 235, 0.9)
  );
  opacity: 0.38;
  filter: blur(10px);
}

.name {
  position: relative;
  font-size: 34px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.meta {
  display: grid;
  gap: 10px;
}

.row {
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  background: rgba(255, 255, 255, 0.75);
}

.k {
  color: var(--app-text-dim);
  font-size: 12px;
}

.v {
  font-weight: 800;
}

@media (max-width: 860px) {
  .profile {
    grid-template-columns: 1fr;
  }
}
</style>

