<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()
const heatmapContainer = ref(null)

const grid = computed(() => {
  return terrainStore.processResult?.grid || null
})

async function renderHeatmap() {
  if (!grid.value) {
    return
  }

  await nextTick()

  if (!heatmapContainer.value) {
    return
  }

  const data = [
    {
      x: grid.value.x,
      y: grid.value.y,
      z: grid.value.z,
      type: 'heatmap',
      colorscale: 'Viridis',
      colorbar: {
        title: 'Height Z',
      },
    },
  ]

  const layout = {
    title: '2D Terrain Heatmap',
    autosize: true,
    margin: {
      l: 60,
      r: 30,
      t: 60,
      b: 60,
    },
    xaxis: {
      title: 'X coordinate',
    },
    yaxis: {
      title: 'Y coordinate',
    },
  }

  const config = {
    responsive: true,
    displaylogo: false,
  }

  Plotly.react(heatmapContainer.value, data, layout, config)
}

watch(grid, renderHeatmap, {
  deep: true,
  flush: 'post',
})

onBeforeUnmount(() => {
  if (heatmapContainer.value) {
    Plotly.purge(heatmapContainer.value)
  }
})
</script>

<template>
  <section v-if="grid" class="card">
    <h2>2D Heatmap</h2>
    <div ref="heatmapContainer" class="heatmap-container"></div>
  </section>
</template>