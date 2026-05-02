import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { setupRouterGuards } from '@/router/guards'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/home' },
  { path: '/login', name: 'Login', component: () => import('@/pages/Login.vue'), meta: { public: true, title: '登录' } },
  { path: '/register', name: 'Register', component: () => import('@/pages/Register.vue'), meta: { public: true, title: '注册' } },
  {
    path: '',
    component: () => import('@/layouts/UserLayout.vue'),
    meta: { requiresAuth: true, role: 'user' },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/pages/Home.vue'),
        meta: { requiresAuth: true, role: 'user', title: '首页' },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { requiresAuth: true, role: 'user', title: '数据看板' },
      },
      {
        path: 'comments',
        name: 'Comments',
        component: () => import('@/pages/Comments.vue'),
        meta: { requiresAuth: true, role: 'user', title: '全部评论' },
      },
      {
        path: 'detail/:id',
        name: 'Detail',
        component: () => import('@/pages/Detail.vue'),
        meta: { requiresAuth: true, role: 'user', title: '详情查询' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/pages/Profile.vue'),
        meta: { requiresAuth: true, role: 'user', title: '个人中心' },
      },
    ],
  },
  { path: '/403', name: 'Forbidden', component: () => import('@/pages/Forbidden.vue'), meta: { public: true, title: '403' } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/pages/NotFound.vue'), meta: { public: true, title: '404' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ left: 0, top: 0 }),
})

setupRouterGuards(router)

export default router
