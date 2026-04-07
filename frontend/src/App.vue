<script setup lang="ts">
import StatusBar from './components/StatusBar.vue'
</script>

<template>
  <div class="app">
    <nav class="navbar">
      <div class="navbar-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <router-link to="/" class="brand-link">SelfLLMWiki</router-link>
      </div>
      <div class="navbar-links">
        <router-link to="/" class="nav-link">
          <span class="nav-icon">📄</span>
          <span class="nav-text">Wiki</span>
        </router-link>
        <router-link to="/graph" class="nav-link">
          <span class="nav-icon">🕸️</span>
          <span class="nav-text">图谱</span>
        </router-link>
        <router-link to="/ingest" class="nav-link">
          <span class="nav-icon">⬇️</span>
          <span class="nav-text">摄入</span>
        </router-link>
        <router-link to="/query" class="nav-link">
          <span class="nav-icon">💬</span>
          <span class="nav-text">查询</span>
        </router-link>
        <router-link to="/lint" class="nav-link">
          <span class="nav-icon">✓</span>
          <span class="nav-text">检查</span>
        </router-link>
        <router-link to="/papers" class="nav-link">
          <span class="nav-icon">📚</span>
          <span class="nav-text">论文</span>
        </router-link>
        <router-link to="/log" class="nav-link">
          <span class="nav-icon">📝</span>
          <span class="nav-text">日志</span>
        </router-link>
        <router-link to="/raw" class="nav-link">
          <span class="nav-icon">📁</span>
          <span class="nav-text">资料</span>
        </router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
    <StatusBar />
  </div>
</template>

<style>
/* 淡雅科技风配色 */
:root {
  /* 主色调 - 淡雅蓝灰 */
  --color-primary: #6366f1;
  --color-primary-light: #818cf8;
  --color-primary-dark: #4f46e5;

  /* 背景色 */
  --color-bg: #fafafa;
  --color-bg-secondary: #f4f4f5;
  --color-bg-tertiary: #e4e4e7;
  --color-bg-card: #ffffff;

  /* 文字色 */
  --color-text: #18181b;
  --color-text-secondary: #52525b;
  --color-text-tertiary: #a1a1aa;

  /* 边框 */
  --color-border: #e4e4e7;
  --color-border-light: #f4f4f5;

  /* 强调色 */
  --color-accent: #6366f1;
  --color-accent-light: #e0e7ff;

  /* 功能色 */
  --color-success: #22c55e;
  --color-success-light: #dcfce7;
  --color-warning: #f59e0b;
  --color-warning-light: #fef3c7;
  --color-danger: #ef4444;
  --color-danger-light: #fee2e2;
  --color-info: #3b82f6;
  --color-info-light: #dbeafe;

  /* 字体 */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

  /* 尺寸 */
  --radius-sm: 4px;
  --radius: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* 阴影 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a {
  color: var(--color-primary);
  text-decoration: none;
  transition: color 0.2s;
}

a:hover {
  color: var(--color-primary-dark);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: var(--radius);
}

::-webkit-scrollbar-thumb {
  background: var(--color-bg-tertiary);
  border-radius: var(--radius);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

/* 通用按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-bg-card);
  color: var(--color-text);
  border-color: var(--color-border);
}

.btn:hover:not(:disabled) {
  background: var(--color-bg-secondary);
  border-color: var(--color-text-tertiary);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.btn-small {
  padding: 4px 10px;
  font-size: 12px;
}

/* 输入框样式 */
input, textarea, select {
  font-family: inherit;
  font-size: 14px;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg-card);
  color: var(--color-text);
  transition: border-color 0.2s, box-shadow 0.2s;
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-accent-light);
}

input::placeholder, textarea::placeholder {
  color: var(--color-text-tertiary);
}

/* 卡片样式 */
.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}

/* 标签样式 */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge-success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.badge-warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.badge-danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.badge-info {
  background: var(--color-info-light);
  color: var(--color-info);
}

/* 提示消息 */
.alert {
  padding: 12px 16px;
  border-radius: var(--radius);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-success {
  background: var(--color-success-light);
  color: #166534;
}

.alert-error {
  background: var(--color-danger-light);
  color: #991b1b;
}

.alert-warning {
  background: var(--color-warning-light);
  color: #92400e;
}

.alert-info {
  background: var(--color-info-light);
  color: #1e40af;
}
</style>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--color-bg);
}

.navbar {
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 40px;
}

.brand-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.brand-icon svg {
  width: 18px;
  height: 18px;
}

.brand-link {
  color: var(--color-text) !important;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.brand-link:hover {
  text-decoration: none;
  color: var(--color-primary) !important;
}

.navbar-links {
  display: flex;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary) !important;
  transition: all 0.2s;
}

.nav-link:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text) !important;
  text-decoration: none;
}

.nav-link.router-link-active,
.nav-link.router-link-exact-active {
  background: var(--color-accent-light);
  color: var(--color-primary) !important;
}

.nav-icon {
  font-size: 16px;
  line-height: 1;
}

.main-content {
  flex: 1;
  overflow: auto;
}
</style>
