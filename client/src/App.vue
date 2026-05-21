<template>
  <div class="flex h-screen bg-bg text-ink">
    <Sidebar>
      <template #footer>
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </template>
    </Sidebar>

    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <FilterBar v-if="$route.path !== '/restocking'" />
      <main class="flex-1 overflow-y-auto">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import Sidebar from './components/Sidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/*
 * Global theme classes — these names existed in the original app and are
 * referenced from every view (Dashboard, Inventory, Orders, etc.). Restyling
 * them in one place is how all 7 views inherit the new look without
 * per-view edits. Values come from CSS variables in styles/tokens.css.
 */

main {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
  letter-spacing: -0.01em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 13px;
}

/* Stat cards — borders not shadows, denser type, smaller numbers. */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-surface);
  padding: 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: border-color 0.15s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
  letter-spacing: 0;
  text-transform: none;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger  .stat-value { color: var(--color-danger); }
.stat-card.info    .stat-value { color: var(--color-accent); }

/* Cards — same Linear-style treatment. */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 16px;
  border: 1px solid var(--color-border);
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.005em;
}

/* Tables */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: transparent;
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: 8px 12px;
  font-weight: 500;
  color: var(--color-text-muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 10px 12px;
  border-top: 1px solid var(--color-border);
  color: var(--color-text);
  font-size: 13px;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-surface-hover);
}

/* Badges — softer, smaller, no uppercase. */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
  border: 1px solid transparent;
}

.badge.success    { background: #ecfdf5; color: #166534; border-color: #d1fae5; }
.badge.warning    { background: #fef3c7; color: #92400e; border-color: #fde68a; }
.badge.danger     { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
.badge.info       { background: var(--color-accent-soft); color: var(--color-accent); border-color: var(--color-accent-soft); }
.badge.increasing { background: #ecfdf5; color: #166534; border-color: #d1fae5; }
.badge.decreasing { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
.badge.stable     { background: var(--color-surface-hover); color: var(--color-text-muted); border-color: var(--color-border); }
.badge.high       { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
.badge.medium     { background: #fef3c7; color: #92400e; border-color: #fde68a; }
.badge.low        { background: var(--color-accent-soft); color: var(--color-accent); border-color: var(--color-accent-soft); }

/* Status messages */
.loading {
  text-align: center;
  padding: 48px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 12px 16px;
  border-radius: var(--radius);
  margin: 16px 0;
  font-size: 13px;
}
</style>
