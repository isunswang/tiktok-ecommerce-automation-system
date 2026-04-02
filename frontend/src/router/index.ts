import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: '商品管理' },
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: '订单管理' },
      },
      {
        path: 'fulfillment',
        name: 'Fulfillment',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: '履约管理' },
      },
      {
        path: 'customer-service',
        name: 'CustomerService',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: '客服管理' },
      },
      {
        path: 'finance',
        name: 'Finance',
        component: () => import('@/views/PlaceholderView.vue'),
        meta: { title: '财务管理' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  if (to.meta.requiresAuth !== false && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && token) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
