import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'wiki',
      component: () => import('./views/WikiView.vue'),
    },
    {
      path: '/wiki/:slug',
      name: 'wiki-page',
      component: () => import('./views/WikiView.vue'),
    },
    {
      path: '/graph',
      name: 'graph',
      component: () => import('./views/GraphView.vue'),
    },
    {
      path: '/ingest',
      name: 'ingest',
      component: () => import('./views/IngestView.vue'),
    },
    {
      path: '/query',
      name: 'query',
      component: () => import('./views/QueryView.vue'),
    },
    {
      path: '/lint',
      name: 'lint',
      component: () => import('./views/LintView.vue'),
    },
    {
      path: '/papers',
      name: 'papers',
      component: () => import('./views/PaperDiscovery.vue'),
    },
    {
      path: '/log',
      name: 'log',
      component: () => import('./views/LogView.vue'),
    },
    {
      path: '/raw',
      name: 'raw',
      component: () => import('./views/RawView.vue'),
    },
  ],
})

export default router
