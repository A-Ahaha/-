<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataLine, House, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const active = computed(() => {
  if (route.path.startsWith('/profile')) return '/profile'
  if (route.path.startsWith('/home')) return '/home'
  if (route.path.startsWith('/dashboard')) return '/dashboard'
  return '/home'
})

const username = computed(() => userStore.userInfo?.username ?? '—')

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

onMounted(() => {
  if (!userStore.userInfo) {
    userStore.getUserInfo().catch(() => null)
  }
})

function onMenuSelect(index: string | number) {
  router.push(String(index))
}
</script>

<template>
  <div class="shell">
    <div class="top app-card">
      <div class="brand" @click="router.push('/home')">
        <div class="mark" />
        <div>
          <div class="brand-title">质量溯源</div>
          <div class="brand-sub">Quality Dashboard</div>
        </div>
      </div>

      <el-menu mode="horizontal" class="menu" :default-active="active" @select="onMenuSelect">
        <el-menu-item index="/home">
          <el-icon><House /></el-icon>
          首页
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          数据看板
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          个人中心
        </el-menu-item>
      </el-menu>

      <div class="right">
        <div class="chip">用户：{{ username }}</div>
        <el-button size="small" type="danger" plain @click="onLogout">退出</el-button>
      </div>
    </div>

    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100%;
  padding: 14px 16px 18px;
}

.top {
  display: grid;
  grid-template-columns: 260px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 10px 12px;
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.mark {
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(6, 182, 212, 0.82));
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
}

.brand-title {
  font-weight: 900;
  letter-spacing: 0.06em;
}

.brand-sub {
  margin-top: 1px;
  font-size: 11px;
  color: rgba(17, 24, 39, 0.55);
}

.menu {
  border-bottom: none;
  background: transparent;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chip {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: rgba(255, 255, 255, 0.9);
  color: rgba(17, 24, 39, 0.68);
}

.content {
  margin-top: 14px;
}

@media (max-width: 980px) {
  .top {
    grid-template-columns: 1fr;
  }
  .right {
    justify-content: space-between;
  }
}
</style>
