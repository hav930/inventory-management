<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="successMessage" class="success-banner">
      <span>{{ successMessage }}</span>
      <router-link to="/orders" class="success-link">{{ t('restocking.viewInOrders') }} →</router-link>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budgetTitle') }}</h3>
        <div class="budget-display">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
      </div>
      <div class="budget-control">
        <input
          type="range"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          v-model.number="budget"
          class="budget-slider"
          :aria-label="t('restocking.budgetTitle')"
        />
        <div class="budget-bounds">
          <span>{{ currencySymbol }}{{ BUDGET_MIN.toLocaleString() }}</span>
          <span>{{ currencySymbol }}{{ BUDGET_MAX.toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          {{ t('restocking.recommendationsTitle') }}
          ({{ selectedCount }} / {{ recommendations.length }})
        </h3>
        <button
          type="button"
          class="place-order-btn"
          :disabled="selectedCount === 0 || submitting || loading || !!successMessage"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="recommendations.length === 0" class="empty">{{ t('restocking.empty') }}</div>

      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th class="col-select">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  :indeterminate.prop="someSelected && !allSelected"
                  @change="toggleAll"
                  :aria-label="t('restocking.selectAll')"
                />
              </th>
              <th>{{ t('inventory.table.sku') }}</th>
              <th>{{ t('inventory.table.itemName') }}</th>
              <th>{{ t('inventory.table.category') }}</th>
              <th class="num">{{ t('restocking.table.onHand') }}</th>
              <th class="num">{{ t('restocking.table.forecasted') }}</th>
              <th class="num">{{ t('restocking.table.shortage') }}</th>
              <th class="num">{{ t('restocking.table.suggested') }}</th>
              <th class="num">{{ t('restocking.table.unitCost') }}</th>
              <th class="num">{{ t('restocking.table.lineTotal') }}</th>
              <th class="num">{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in recommendations"
              :key="r.sku"
              :class="{ 'row-deselected': !selectedSkus.has(r.sku) }"
            >
              <td class="col-select">
                <input
                  type="checkbox"
                  :checked="selectedSkus.has(r.sku)"
                  @change="toggleSku(r.sku)"
                  :aria-label="t('restocking.selectRow', { sku: r.sku })"
                />
              </td>
              <td><strong>{{ r.sku }}</strong></td>
              <td>{{ translateProductName(r.name) }}</td>
              <td>{{ translateCategory(r.category) }}</td>
              <td class="num">{{ r.quantity_on_hand.toLocaleString() }}</td>
              <td class="num">{{ r.forecasted_demand.toLocaleString() }}</td>
              <td class="num"><strong>{{ r.shortage.toLocaleString() }}</strong></td>
              <td class="num"><strong>{{ r.suggested_quantity.toLocaleString() }}</strong></td>
              <td class="num">{{ currencySymbol }}{{ r.unit_cost.toFixed(2) }}</td>
              <td class="num"><strong>{{ currencySymbol }}{{ formatCurrency(r.line_total) }}</strong></td>
              <td class="num">{{ r.lead_time_days }} {{ t('restocking.days') }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="9" class="total-label">{{ t('restocking.runningTotal') }}</td>
              <td class="num total-value"><strong>{{ currencySymbol }}{{ formatCurrency(runningTotal) }}</strong></td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { useSubmittedOrders } from '../composables/useSubmittedOrders'

const BUDGET_MIN = 1000
const BUDGET_MAX = 500000
const BUDGET_STEP = 1000
const DEFAULT_BUDGET = 50000
const DEBOUNCE_MS = 300

// Module-scoped so it survives route changes (the component unmounts when the
// user leaves the tab, and a setup-scoped ref would reset to DEFAULT_BUDGET).
// Same singleton pattern as useFilters.js.
const budget = ref(DEFAULT_BUDGET)

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()
    const { submitOrder } = useSubmittedOrders()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(false)
    const error = ref(null)
    const recommendations = ref([])
    const submitting = ref(false)
    const successMessage = ref('')
    // Tracks the SKUs the user has opted in for the current order. Reset to "all"
    // every time recommendations reload — selection isn't meaningful once the
    // underlying recommendation set has changed.
    const selectedSkus = ref(new Set())

    const selectedRecommendations = computed(() =>
      recommendations.value.filter(r => selectedSkus.value.has(r.sku))
    )
    const selectedCount = computed(() => selectedRecommendations.value.length)
    const allSelected = computed(() =>
      recommendations.value.length > 0 && selectedCount.value === recommendations.value.length
    )
    const someSelected = computed(() => selectedCount.value > 0)
    const runningTotal = computed(() =>
      selectedRecommendations.value.reduce((sum, r) => sum + r.line_total, 0)
    )

    // Set mutations aren't tracked by Vue's ref reactivity, so replace the Set
    // on every change to trigger updates.
    const toggleSku = (sku) => {
      const next = new Set(selectedSkus.value)
      if (next.has(sku)) next.delete(sku)
      else next.add(sku)
      selectedSkus.value = next
    }
    const toggleAll = () => {
      selectedSkus.value = allSelected.value
        ? new Set()
        : new Set(recommendations.value.map(r => r.sku))
    }

    const formatCurrency = (n) =>
      Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const translateCategory = (category) => {
      const map = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies'),
      }
      return map[category] || category
    }

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockingRecommendations(budget.value)
        selectedSkus.value = new Set(recommendations.value.map(r => r.sku))
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    let debounceTimer = null
    watch(budget, () => {
      // Debounce: dragging the slider would otherwise fire one request per tick.
      if (debounceTimer) clearTimeout(debounceTimer)
      successMessage.value = ''
      debounceTimer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    })

    const placeOrder = async () => {
      if (selectedRecommendations.value.length === 0) return
      try {
        submitting.value = true
        error.value = null
        const payload = {
          budget: budget.value,
          items: selectedRecommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.suggested_quantity,
            unit_cost: r.unit_cost,
            lead_time_days: r.lead_time_days,
            line_total: r.line_total,
          })),
        }
        const order = await submitOrder(payload)
        successMessage.value = t('restocking.placed', { orderNumber: order.order_number })
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)
    onUnmounted(() => {
      // Drop any pending debounced fetch — its callback would update setup-scoped
      // refs (recommendations, loading) on an already-destroyed component.
      if (debounceTimer) clearTimeout(debounceTimer)
    })

    return {
      t,
      budget,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      loading,
      error,
      recommendations,
      runningTotal,
      submitting,
      successMessage,
      placeOrder,
      currencySymbol,
      translateProductName,
      translateCategory,
      formatCurrency,
      selectedSkus,
      selectedCount,
      allSelected,
      someSelected,
      toggleSku,
      toggleAll,
    }
  }
}
</script>

<style scoped>
.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.02em;
}

.budget-control {
  padding: 0.5rem 0.25rem 0;
}

.budget-slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 22px;
  height: 22px;
  background: #2563eb;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);
  transition: transform 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.budget-slider::-moz-range-thumb {
  width: 22px;
  height: 22px;
  background: #2563eb;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);
}

.budget-bounds {
  display: flex;
  justify-content: space-between;
  margin-top: 0.625rem;
  font-size: 0.75rem;
  color: #64748b;
}

.place-order-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.25rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.empty {
  padding: 2.5rem 1rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.num {
  text-align: right;
}

.col-select {
  width: 36px;
  text-align: center;
}

.col-select input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #2563eb;
}

.row-deselected td {
  opacity: 0.4;
}

.row-deselected td.col-select {
  opacity: 1;
}

tfoot td {
  border-top: 2px solid #e2e8f0;
  padding: 0.75rem;
  font-size: 0.875rem;
}

.total-label {
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.75rem;
  text-align: right;
  font-weight: 600;
}

.total-value {
  font-size: 1rem;
  color: #0f172a;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #34d399;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 10px;
  margin-bottom: 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 0.938rem;
}

.success-link {
  color: #065f46;
  text-decoration: underline;
  font-weight: 600;
}
</style>
