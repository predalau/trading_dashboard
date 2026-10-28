import { createRouter, createWebHistory } from 'vue-router'
import Home from '../pages/Home.vue'
import Dashboard from '../pages/Dashboard.vue'
import Trades from '../pages/Trades.vue'
import Profile from '../pages/Profile.vue'
import Backtest from '../pages/Backtest.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/trades',
    name: 'Trades',
    component: Trades
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: Backtest
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
