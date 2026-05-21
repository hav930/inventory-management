import { ref } from 'vue'
import { api } from '../api'

// Singleton state shared across views, mirroring the useFilters() pattern.
// Restocking.vue writes here on submit; Orders.vue reads from here for its
// "Submitted Orders" section so the new order appears without a refresh.
const submittedOrders = ref([])
const loaded = ref(false)

export function useSubmittedOrders() {
  const loadSubmitted = async () => {
    submittedOrders.value = await api.getSubmittedRestockingOrders()
    loaded.value = true
  }

  const submitOrder = async (payload) => {
    const order = await api.submitRestockingOrder(payload)
    submittedOrders.value = [order, ...submittedOrders.value]
    return order
  }

  return { submittedOrders, loaded, loadSubmitted, submitOrder }
}
