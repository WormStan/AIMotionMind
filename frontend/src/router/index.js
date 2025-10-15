import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('../views/Upload.vue'),
    meta: { title: '上传分析' }
  },
  {
    path: '/analysis/:taskId',
    name: 'Analysis',
    component: () => import('../views/Analysis.vue'),
    meta: { title: '分析中' }
  },
  {
    path: '/result/:analysisId',
    name: 'Result',
    component: () => import('../views/Result.vue'),
    meta: { title: '分析结果' }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue'),
    meta: { title: '历史记录' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  NProgress.start()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - AIMotionMind`
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
