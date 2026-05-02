<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { BellFilled, Goods, HomeFilled, Setting, UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const permissionStore = usePermissionStore()

const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/admin/alerts')) return '/admin/alerts'
  if (p.startsWith('/admin/users')) return '/admin/users'
  if (p.startsWith('/admin/products')) return '/admin/products'
  if (p.startsWith('/admin/settings')) return '/admin/settings'
  if (p.startsWith('/admin/profile')) return '/admin/profile'
  return '/admin'
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

function onMenuSelect(index: string) {
  router.push(index)
}

onMounted(() => {
  if (!userStore.userInfo) {
    userStore.getUserInfo().catch(() => null)
  }
})
</script>

<template>
  <el-container class="app-shell">
    <el-aside class="aside" width="248px">
      <div class="brand">
        <div class="brand-mark-wrap">
          <div class="mark" />
        </div>
        <div class="brand-text">
          <div class="brand-title">质量溯源</div>
          <div class="brand-sub">Admin Console</div>
        </div>
      </div>

      <el-menu class="menu" :default-active="activeMenu" @select="onMenuSelect">
        <el-menu-item index="/admin">
          <el-icon>
            <HomeFilled />
          </el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/admin/alerts">
          <el-icon>
            <BellFilled />
          </el-icon>
          <span>预警中心</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon>
            <UserFilled />
          </el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/products">
          <el-icon>
            <Goods />
          </el-icon>
          <span>商品管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/settings">
          <el-icon>
            <Setting />
          </el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>

      <div class="aside-foot app-card">
        <div class="foot-user">
          <div class="dot" />
          <div class="foot-meta">
            <div class="foot-name">{{ username }}</div>
            <div class="foot-role">admin</div>
          </div>
        </div>
        <div class="foot-actions">
          <el-button size="small" @click="router.push('/admin/profile')">个人中心</el-button>
          <el-button size="small" type="danger" plain @click="onLogout">退出</el-button>
        </div>
      </div>
    </el-aside>

    <el-container class="main">
      <el-header class="header">
        <div class="header-left">
          <div class="header-breadcrumb">质量看板 / 管理后台</div>
          <div class="header-title">{{ (route.meta.title as string) || '概览' }}</div>
          <div class="header-desc">商品质量问题发现与溯源系统</div>
        </div>
        <div class="header-right">
          <div class="chip">Real API</div>
          <div class="chip chip-2">{{ permissionStore.adminMenus.length }} 菜单</div>
        </div>
      </el-header>
      <el-main class="content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.aside {
  padding: 18px 14px 14px;
  border-right: 1px solid rgba(17, 24, 39, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.72));
  backdrop-filter: blur(14px);
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 6px 8px 14px;
}

.brand-mark-wrap {
  border-radius: 16px;
  padding: 2px;
  background: linear-gradient(140deg, rgba(37, 99, 235, 0.24), rgba(6, 182, 212, 0.22));
}

.mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(6, 182, 212, 0.8));
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.12);
}

.brand-title {
  font-weight: 900;
  letter-spacing: 0.06em;
}

.brand-sub {
  margin-top: 2px;
  font-size: 11px;
  color: rgba(17, 24, 39, 0.55);
  letter-spacing: 0.06em;
}

.menu {
  border-right: none;
  background: transparent;
}

.menu :deep(.el-menu-item) {
  margin: 4px 4px;
  border-radius: 10px;
  height: 42px;
  line-height: 42px;
}

.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.14), rgba(6, 182, 212, 0.08));
}

.aside-foot {
  margin-top: 12px;
  padding: 12px;
}

.foot-user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.95);
  box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.14);
}

.foot-name {
  font-weight: 800;
}

.foot-role {
  margin-top: 1px;
  font-size: 11px;
  color: rgba(17, 24, 39, 0.6);
}

.foot-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.main {
  background: transparent;
}

.header {
  height: 74px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  padding: 0 20px;
}

.header-breadcrumb {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(17, 24, 39, 0.52);
}

.header-title {
  margin-top: 3px;
  font-weight: 900;
  letter-spacing: 0.02em;
}

.header-desc {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(17, 24, 39, 0.58);
}

.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chip {
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: rgba(255, 255, 255, 0.9);
  color: rgba(17, 24, 39, 0.68);
}

.chip-2 {
  background: rgba(37, 99, 235, 0.06);
  border-color: rgba(37, 99, 235, 0.14);
}

.content {
  padding: 18px 20px 20px;
}
</style>
