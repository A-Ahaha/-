import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { setupRouterGuards } from '@/router/guards'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/admin',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/pages/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/pages/admin/Dashboard.vue'),
        meta: { requiresAuth: true, role: 'admin', title: '概览' },
      },
      {
        path: 'alerts',
        name: 'AlertCenter',
        component: () => import('@/pages/admin/AlertCenter.vue'),
        meta: { requiresAuth: true, role: 'admin', title: '预警中心' },
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/pages/admin/UserManagement.vue'),
        meta: { requiresAuth: true, role: 'admin', title: '用户管理' },
      },
      {
        path: 'products',
        name: 'ProductManagement',
        component: () => import('@/pages/admin/ProductManagement.vue'),
        meta: { requiresAuth: true, role: 'admin', title: '商品管理' },
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/pages/admin/SystemSettings.vue'),
        meta: { requiresAuth: true, role: 'admin', title: '系统设置' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/pages/admin/Profile.vue'),
        meta: { requiresAuth: true, role: 'admin', title: '个人中心' },
      },
    ],
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/pages/Forbidden.vue'),
    meta: { public: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ left: 0, top: 0 }),
})

setupRouterGuards(router)

export default router
