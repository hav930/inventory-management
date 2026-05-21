import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './styles/tokens.css'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'
import Restocking from './views/Restocking.vue'

// Route meta drives the Sidebar's nav list — adding a route here automatically
// shows it in the sidebar via the labelKey lookup.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { labelKey: 'nav.overview' } },
    { path: '/inventory', component: Inventory, meta: { labelKey: 'nav.inventory' } },
    { path: '/orders', component: Orders, meta: { labelKey: 'nav.orders' } },
    { path: '/demand', component: Demand, meta: { labelKey: 'nav.demandForecast' } },
    { path: '/restocking', component: Restocking, meta: { labelKey: 'nav.restocking' } },
    { path: '/spending', component: Spending, meta: { labelKey: 'nav.finance' } },
    { path: '/reports', component: Reports, meta: { labelKey: 'nav.reports' } }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
