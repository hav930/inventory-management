<template>
  <aside class="w-60 shrink-0 h-screen bg-surface border-r border-border flex flex-col">
    <!-- Brand block -->
    <div class="h-14 px-4 flex items-center gap-2 border-b border-border">
      <div class="w-7 h-7 rounded-md bg-ink flex items-center justify-center text-white text-xs font-semibold">
        {{ brandInitial }}
      </div>
      <div class="min-w-0">
        <div class="text-sm font-semibold text-ink leading-tight truncate">{{ t('nav.companyName') }}</div>
        <div class="text-xs text-ink-muted leading-tight truncate">{{ t('nav.subtitle') }}</div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 overflow-y-auto px-2 py-3">
      <ul class="space-y-0.5">
        <li v-for="item in navItems" :key="item.to">
          <router-link
            :to="item.to"
            class="flex items-center gap-2 px-2.5 py-1.5 rounded-md text-sm text-ink-muted hover:bg-surface-hover hover:text-ink transition-colors"
            active-class="bg-surface-hover text-ink font-medium"
            :exact-active-class="item.to === '/' ? 'bg-surface-hover text-ink font-medium' : ''"
          >
            <component :is="item.icon" class="w-4 h-4 shrink-0" />
            <span class="truncate">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Footer: language + profile -->
    <div class="border-t border-border p-2 space-y-1">
      <slot name="footer" />
    </div>
  </aside>
</template>

<script>
import { computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../composables/useI18n'

// Inline SVG icons keep the dependency surface flat. Each is a render
// function that produces a stroked 16x16 lucide-style glyph.
const icon = (paths) => ({
  render: () => h('svg', {
    width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none',
    stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
  }, paths.map(d => h('path', { d })))
})
const Icons = {
  overview: icon([
    'M3 3h7v9H3z',
    'M14 3h7v5h-7z',
    'M14 12h7v9h-7z',
    'M3 16h7v5H3z',
  ]),
  inventory: icon([
    'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z',
    'M3.27 6.96 12 12.01l8.73-5.05',
    'M12 22.08V12',
  ]),
  orders: icon([
    'M9 11V6a3 3 0 0 1 6 0v5',
    'M5 9h14l-1 12H6L5 9z',
  ]),
  finance: icon([
    'M12 1v22',
    'M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
  ]),
  demand: icon([
    'M3 3v18h18',
    'M7 14l4-4 4 4 5-5',
  ]),
  restocking: icon([
    'M3 6h18',
    'M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6',
    'M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2',
    'M10 11v6',
    'M14 11v6',
  ]),
  reports: icon([
    'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z',
    'M14 2v6h6',
    'M9 13h6',
    'M9 17h4',
  ]),
}

const ICON_FOR_LABELKEY = {
  'nav.overview': Icons.overview,
  'nav.inventory': Icons.inventory,
  'nav.orders': Icons.orders,
  'nav.finance': Icons.finance,
  'nav.demandForecast': Icons.demand,
  'nav.restocking': Icons.restocking,
  'nav.reports': Icons.reports,
}

export default {
  name: 'Sidebar',
  setup() {
    const router = useRouter()
    const { t } = useI18n()

    const navItems = computed(() =>
      router.getRoutes()
        .filter(r => r.meta?.labelKey)
        .map(r => ({
          to: r.path,
          label: t(r.meta.labelKey),
          icon: ICON_FOR_LABELKEY[r.meta.labelKey],
        }))
    )

    const brandInitial = computed(() =>
      (t('nav.companyName') || '?').trim().charAt(0).toUpperCase()
    )

    return { navItems, brandInitial, t }
  },
}
</script>
