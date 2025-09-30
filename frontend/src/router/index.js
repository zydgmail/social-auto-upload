import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import AccountManagement from '../views/AccountManagement.vue'
import MaterialManagement from '../views/MaterialManagement.vue'
import CoverGenerator from '../views/CoverGenerator.vue'
import PublishCenter from '../views/PublishCenter.vue'
import About from '../views/About.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/account-management',
    name: 'AccountManagement',
    component: AccountManagement
  },
  {
    path: '/material-management',
    redirect: '/material-management/list'
  },
  {
    path: '/material-management/list',
    name: 'MaterialList',
    component: MaterialManagement
  },
  {
    path: '/material-management/cover',
    name: 'CoverGenerator',
    component: CoverGenerator
  },
  {
    path: '/publish-center',
    name: 'PublishCenter',
    component: PublishCenter
  },
  {
    path: '/about',
    name: 'About',
    component: About
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router