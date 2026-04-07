<script setup lang="ts">
import { useAppStore } from '../stores/app'

const store = useAppStore()
</script>

<template>
  <footer class="status-bar">
    <div class="status-left">
      <span class="status-badge">
        <span class="status-dot"></span>
        系统就绪
      </span>
      <span class="status-divider"></span>
      <span class="status-item">
        <span class="status-label">页面</span>
        <span class="status-value">{{ store.pageCount }}</span>
      </span>
    </div>
    <div class="status-right">
      <span class="status-item" v-if="store.lastAction">
        <span class="status-label">最近操作</span>
        <span class="status-value">{{ store.lastAction }}</span>
      </span>
    </div>
  </footer>
</template>

<style scoped>
.status-bar {
  background: var(--color-bg-card);
  border-top: 1px solid var(--color-border);
  padding: 0 20px;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  height: 36px;
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--color-success-light);
  color: var(--color-success);
  border-radius: 9999px;
  font-weight: 500;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-divider {
  width: 1px;
  height: 16px;
  background: var(--color-border);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-secondary);
}

.status-label {
  font-weight: 500;
}

.status-value {
  color: var(--color-text);
  font-weight: 600;
}
</style>
