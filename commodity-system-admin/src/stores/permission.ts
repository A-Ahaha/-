import { defineStore } from 'pinia'
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

export interface AdminMenuItem {
  key: string
  label: string
  path: string
}

export const usePermissionStore = defineStore('permission', () => {
  const userStore = useUserStore()

  const adminMenus = computed<AdminMenuItem[]>(() => {
    if (userStore.role !== 'admin') return []
    return [
      { key: 'dashboard', label: '概览', path: '/admin' },
      { key: 'alerts', label: '预警中心', path: '/admin/alerts' },
      { key: 'users', label: '用户管理', path: '/admin/users' },
      { key: 'settings', label: '系统设置', path: '/admin/settings' },
    ]
  })

  return { adminMenus }
})
