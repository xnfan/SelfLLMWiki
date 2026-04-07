<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as d3 from 'd3'
import { fetchGraph, type GraphData } from '../api/client'

const router = useRouter()

const svgRef = ref<SVGSVGElement | null>(null)
const searchQuery = ref('')
const loading = ref(true)
const graphData = ref<GraphData | null>(null)

const categoryColors: Record<string, string> = {
  concept: '#4a90d9',
  paper: '#27ae60',
  entity: '#e67e22',
  source: '#95a5a6',
  missing: '#e74c3c',
}

let simulation: d3.Simulation<any, any> | null = null

function buildGraph(data: GraphData) {
  if (!svgRef.value) return

  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  const container = svg.node()!.parentElement!
  const width = container.clientWidth
  const height = container.clientHeight

  svg.attr('width', width).attr('height', height)

  const g = svg.append('g')

  // 缩放
  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom)

  const nodes = data.nodes.map(d => ({ ...d }))
  const edges = data.edges.map(d => ({ ...d }))

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id((d: any) => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius((d: any) => (d.size || 1) * 5 + 10))

  // 边
  const link = g.append('g')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('stroke', '#ccc')
    .attr('stroke-width', 1)
    .attr('stroke-opacity', 0.6)

  // 节点组
  const node = g.append('g')
    .selectAll<SVGGElement, any>('g')
    .data(nodes)
    .join('g')
    .attr('class', 'node-group')
    .style('cursor', 'pointer')

  // 圆形
  node.append('circle')
    .attr('r', (d: any) => Math.max(6, (d.size || 1) * 4))
    .attr('fill', (d: any) => categoryColors[d.category] || '#999')
    .attr('stroke', (d: any) => d.category === 'missing' ? '#e74c3c' : 'white')
    .attr('stroke-width', (d: any) => d.category === 'missing' ? 2 : 1.5)
    .attr('stroke-dasharray', (d: any) => d.category === 'missing' ? '4,2' : 'none')

  // 标签
  node.append('text')
    .text((d: any) => d.label)
    .attr('x', 0)
    .attr('y', (d: any) => Math.max(6, (d.size || 1) * 4) + 14)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .attr('pointer-events', 'none')

  // 悬停高亮
  node.on('mouseover', function (_event, d: any) {
    d3.select(this).select('circle')
      .transition().duration(150)
      .attr('r', Math.max(6, (d.size || 1) * 4) + 3)
      .attr('stroke-width', 3)

    const connectedIds = new Set<string>()
    connectedIds.add(d.id)
    edges.forEach((e: any) => {
      const src = typeof e.source === 'object' ? e.source.id : e.source
      const tgt = typeof e.target === 'object' ? e.target.id : e.target
      if (src === d.id) connectedIds.add(tgt)
      if (tgt === d.id) connectedIds.add(src)
    })

    node.style('opacity', (n: any) => connectedIds.has(n.id) ? 1 : 0.2)
    link.style('opacity', (l: any) => {
      const src = typeof l.source === 'object' ? l.source.id : l.source
      const tgt = typeof l.target === 'object' ? l.target.id : l.target
      return src === d.id || tgt === d.id ? 1 : 0.1
    })
  })

  node.on('mouseout', function (_event, d: any) {
    d3.select(this).select('circle')
      .transition().duration(150)
      .attr('r', Math.max(6, (d.size || 1) * 4))
      .attr('stroke-width', d.category === 'missing' ? 2 : 1.5)

    node.style('opacity', 1)
    link.style('opacity', 0.6)
  })

  // 点击导航
  node.on('click', (_event, d: any) => {
    router.push(`/wiki/${encodeURIComponent(d.id)}`)
  })

  // 拖拽
  const drag = d3.drag<SVGGElement, any>()
    .on('start', (event, d) => {
      if (!event.active) simulation!.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    })
    .on('drag', (event, d) => {
      d.fx = event.x
      d.fy = event.y
    })
    .on('end', (event, d) => {
      if (!event.active) simulation!.alphaTarget(0)
      d.fx = null
      d.fy = null
    })

  node.call(drag)

  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })
}

// 搜索过滤
watch(searchQuery, (q) => {
  if (!svgRef.value) return
  const svg = d3.select(svgRef.value)
  const lower = q.toLowerCase()

  if (!lower) {
    svg.selectAll('.node-group').style('opacity', 1)
    return
  }

  svg.selectAll<SVGGElement, any>('.node-group')
    .style('opacity', (d: any) => {
      return d.label.toLowerCase().includes(lower) || d.id.toLowerCase().includes(lower) ? 1 : 0.15
    })
})

async function loadGraph() {
  loading.value = true
  try {
    const res = await fetchGraph()
    graphData.value = res.data
    buildGraph(res.data)
  } catch (e) {
    console.error('加载图谱失败', e)
  } finally {
    loading.value = false
  }
}

function handleResize() {
  if (graphData.value) {
    buildGraph(graphData.value)
  }
}

onMounted(() => {
  loadGraph()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (simulation) simulation.stop()
})
</script>

<template>
  <div class="graph-container">
    <div class="graph-controls">
      <input
        v-model="searchQuery"
        placeholder="搜索节点..."
        class="graph-search"
      />
      <div class="legend">
        <span class="legend-item">
          <span class="dot" style="background: #4a90d9"></span>概念
        </span>
        <span class="legend-item">
          <span class="dot" style="background: #27ae60"></span>论文
        </span>
        <span class="legend-item">
          <span class="dot" style="background: #e67e22"></span>实体
        </span>
        <span class="legend-item">
          <span class="dot" style="background: #95a5a6"></span>来源
        </span>
        <span class="legend-item">
          <span class="dot dot-missing" style="background: transparent; border: 2px dashed #e74c3c"></span>缺失
        </span>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">加载图谱中...</div>

    <svg ref="svgRef" class="graph-svg"></svg>
  </div>
</template>

<style scoped>
.graph-container {
  position: relative;
  width: 100%;
  height: calc(100vh - 80px);
  overflow: hidden;
  background: #fafbfc;
}

.graph-controls {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.graph-search {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 14px;
  width: 220px;
  background: white;
  box-shadow: var(--shadow);
}

.graph-search:focus {
  outline: none;
  border-color: var(--color-accent);
}

.legend {
  background: white;
  padding: 8px 12px;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.dot-missing {
  box-sizing: border-box;
}

.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  color: var(--color-text-light);
}

.graph-svg {
  width: 100%;
  height: 100%;
}
</style>
