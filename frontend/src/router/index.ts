import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/hub',
    name: 'Hub',
    component: () => import('@/views/HubView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/works',
    name: 'Works',
    component: () => import('@/views/WorksView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/UploadView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/segment/:id',
    name: 'Segment',
    component: () => import('@/views/SegmentView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/music',
    name: 'Music',
    component: () => import('@/views/MusicView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/works/:workId/segments',
    name: 'SegmentsByWork',
    component: () => import('@/views/SegmentsByWorkView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
