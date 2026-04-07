<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'

const props = defineProps<{
  content: string
}>()

const router = useRouter()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  breaks: true,
})

// 处理 [[wikilinks]]
function processWikilinks(text: string): string {
  return text.replace(/\[\[([^\]]+)\]\]/g, (_match, link: string) => {
    const parts = link.split('|')
    const slug = parts[0].trim()
    const label = (parts[1] || parts[0]).trim()
    return `<a class="wikilink" data-slug="${slug}" href="/wiki/${encodeURIComponent(slug)}">${label}</a>`
  })
}

const rendered = computed(() => {
  const withLinks = processWikilinks(props.content || '')
  return md.render(withLinks)
})

function handleClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.classList.contains('wikilink')) {
    e.preventDefault()
    const slug = target.getAttribute('data-slug')
    if (slug) {
      router.push(`/wiki/${encodeURIComponent(slug)}`)
    }
  }
}
</script>

<template>
  <div class="markdown-body" v-html="rendered" @click="handleClick"></div>
</template>

<style scoped>
.markdown-body {
  line-height: 1.7;
  font-size: 15px;
}

.markdown-body :deep(h1) {
  font-size: 1.8em;
  margin: 0.8em 0 0.4em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--color-border);
}

.markdown-body :deep(h2) {
  font-size: 1.5em;
  margin: 0.7em 0 0.3em;
  padding-bottom: 0.2em;
  border-bottom: 1px solid var(--color-border);
}

.markdown-body :deep(h3) {
  font-size: 1.25em;
  margin: 0.6em 0 0.3em;
}

.markdown-body :deep(p) {
  margin: 0.6em 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.8em;
  margin: 0.5em 0;
}

.markdown-body :deep(code) {
  background: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background: var(--color-bg-secondary);
  padding: 12px 16px;
  border-radius: var(--radius);
  overflow-x: auto;
  margin: 0.6em 0;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: none;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--color-accent);
  margin: 0.6em 0;
  padding: 0.5em 1em;
  color: var(--color-text-light);
  background: var(--color-bg-secondary);
  border-radius: 0 var(--radius) var(--radius) 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.6em 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--color-border);
  padding: 8px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--color-bg-secondary);
  font-weight: 600;
}

.markdown-body :deep(.wikilink) {
  color: var(--color-accent);
  border-bottom: 1px dashed var(--color-accent);
  cursor: pointer;
}

.markdown-body :deep(.wikilink:hover) {
  border-bottom-style: solid;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: var(--radius);
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1em 0;
}
</style>
