import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw } from 'vue-router';

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/views/documents/DocumentList.vue'),
    meta: { title: '文档管理' },
  },
  {
    path: '/documents/:id/versions',
    name: 'DocumentVersions',
    component: () => import('@/views/documents/DocumentVersions.vue'),
    meta: { title: '版本历史' },
  },
  {
    path: '/documents/versions/:versionId',
    name: 'VersionDetail',
    component: () => import('@/views/documents/VersionDetail.vue'),
    meta: { title: '版本详情' },
  },
  {
    path: '/documents/compare',
    name: 'VersionCompare',
    component: () => import('@/views/documents/VersionCompare.vue'),
    meta: { title: '版本对比' },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/chat/ChatView.vue'),
    meta: { title: '智能问答' },
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/search/SearchView.vue'),
    meta: { title: '语义检索' },
  },
  {
    path: '/training',
    name: 'Training',
    component: () => import('@/views/training/TrainingView.vue'),
    meta: { title: '培训任务' },
  },
  {
    path: '/review',
    name: 'Review',
    component: () => import('@/views/review/ReviewView.vue'),
    meta: { title: '审批中心' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/settings/SettingsView.vue'),
    meta: { title: '系统设置' },
  },
  // 404 页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' },
  },
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    // 始终滚动到顶部
    return { top: 0 };
  },
});

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  const title = to.meta.title as string;
  if (title) {
    document.title = `${title} - QMS-Nexus`;
  } else {
    document.title = 'QMS-Nexus - 医疗器械文档管理系统';
  }
  next();
});

export default router;
