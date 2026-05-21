<template>
  <div class="profile-menu">
    <button
      class="profile-button"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <div class="avatar">
        {{ getInitials(currentUser.name) }}
      </div>
      <span class="profile-name">{{ currentUser.name }}</span>
      <svg
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu">
      <div class="dropdown-header">
        <div class="avatar-large">
          {{ getInitials(currentUser.name) }}
        </div>
        <div class="user-info">
          <div class="user-name">{{ currentUser.name }}</div>
          <div class="user-email">{{ currentUser.email }}</div>
        </div>
      </div>

      <div class="dropdown-divider"></div>

      <button
        class="dropdown-item"
        @mousedown.prevent="showProfileDetails"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 9C10.6569 9 12 7.65685 12 6C12 4.34315 10.6569 3 9 3C7.34315 3 6 4.34315 6 6C6 7.65685 7.34315 9 9 9Z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M15 15C15 12.7909 12.3137 11 9 11C5.68629 11 3 12.7909 3 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        {{ t('profile.profileDetails') }}
      </button>

      <button
        class="dropdown-item"
        @mousedown.prevent="showTasks"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M15 3H3C2.44772 3 2 3.44772 2 4V14C2 14.5523 2.44772 15 3 15H15C15.5523 15 16 14.5523 16 14V4C16 3.44772 15.5523 3 15 3Z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M6 7L8 9L12 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('profile.myTasks') }}
        <span v-if="pendingTaskCount > 0" class="task-badge">{{ pendingTaskCount }}</span>
      </button>

      <div class="dropdown-divider"></div>

      <button
        class="dropdown-item logout"
        @mousedown.prevent="handleLogout"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M7 15H4C3.44772 15 3 14.5523 3 14V4C3 3.44772 3.44772 3 4 3H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M11 12L15 9M15 9L11 6M15 9H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('profile.logout') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, logout, getInitials } = useAuth()
const { t } = useI18n()

const isDropdownOpen = ref(false)
const emit = defineEmits(['show-profile-details', 'show-tasks'])

const pendingTaskCount = computed(() => {
  return currentUser.value.tasks.filter(task => task.status === 'pending').length
})

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const showProfileDetails = () => {
  isDropdownOpen.value = false
  emit('show-profile-details')
}

const showTasks = () => {
  isDropdownOpen.value = false
  emit('show-tasks')
}

const handleLogout = () => {
  isDropdownOpen.value = false
  logout()
}
</script>

<style scoped>
.profile-menu {
  position: relative;
}

/* Sidebar-footer placement: full-width trigger, transparent until hover. */
.profile-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  color: var(--color-text);
}

.profile-button:hover {
  background: var(--color-surface-hover);
}

.avatar {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--color-ink, var(--color-text));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 10px;
  flex-shrink: 0;
}

.profile-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
  flex: 1;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chevron {
  color: var(--color-text-subtle);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

/* Dropdown opens UPWARD from the sidebar footer. */
.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  right: 0;
  min-width: 240px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-header {
  padding: 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  background: var(--color-surface-hover);
  border-bottom: 1px solid var(--color-border);
}

.avatar-large {
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  background: var(--color-text);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--color-text);
  font-size: 13px;
  margin-bottom: 2px;
}

.user-email {
  font-size: 12px;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  background: var(--color-border);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 13px;
  font-weight: 400;
  color: var(--color-text);
}

.dropdown-item:hover {
  background: var(--color-surface-hover);
}

.dropdown-item svg {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.dropdown-item.logout {
  color: var(--color-danger);
}

.dropdown-item.logout svg {
  color: var(--color-danger);
}

.dropdown-item.logout:hover {
  background: #fef2f2;
}

.task-badge {
  margin-left: auto;
  background: var(--color-accent);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}
</style>
