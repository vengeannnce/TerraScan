<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()
const heatmapContainer = ref(null)
const mapMode = ref('smooth')

const grid = computed(() => {
  return terrainStore.processResult?.grid || null
})

const RANGE_COLORS = [
  '#2563eb', // blue
  '#0891b2', // cyan
  '#16a34a', // green
  '#84cc16', // light green
  '#facc15', // yellow
  '#f97316', // orange
  '#dc2626', // red
]

function getZRange(zMatrix) {
  let min = Infinity
  let max = -Infinity

  for (let row = 0; row < zMatrix.length; row += 1) {
    for (let col = 0; col < zMatrix[row].length; col += 1) {
      const value = zMatrix[row][col]

      if (value < min) min = value
      if (value > max) max = value
    }
  }

  return { min, max }
}

function createElevationColorscale() {
  return [
    [0.0, '#2563eb'],
    [0.14, '#2563eb'],

    [0.14, '#0891b2'],
    [0.28, '#0891b2'],

    [0.28, '#16a34a'],
    [0.42, '#16a34a'],

    [0.42, '#84cc16'],
    [0.56, '#84cc16'],

    [0.56, '#facc15'],
    [0.70, '#facc15'],

    [0.70, '#f97316'],
    [0.84, '#f97316'],

    [0.84, '#dc2626'],
    [1.0, '#dc2626'],
  ]
}

function createRangeBands(min, max, bandCount = 7) {
  const bands = []

  if (min === max) {
    return [
      {
        from: min,
        to: max,
        color: RANGE_COLORS[0],
        label: `${min.toFixed(2)} — ${max.toFixed(2)}`,
      },
    ]
  }

  const step = (max - min) / bandCount

  for (let index = 0; index < bandCount; index += 1) {
    const from = min + step * index
    const to = index === bandCount - 1 ? max : min + step * (index + 1)

    bands.push({
      from,
      to,
      color: RANGE_COLORS[index % RANGE_COLORS.length],
      label: `${from.toFixed(1)} — ${to.toFixed(1)}`,
    })
  }

  return bands
}

const rangeBands = computed(() => {
  if (!grid.value) {
    return []
  }

  const { min, max } = getZRange(grid.value.z)
  return createRangeBands(min, max, 7)
})

function buildProfileData(gridData) {
  const centerRowIndex = Math.floor(gridData.z.length / 2)
  const profileX = gridData.x
  const profileZ = gridData.z[centerRowIndex]

  return {
    x: profileX,
    z: profileZ,
  }
}

function buildProfileShapes(bands, xMin, xMax) {
  return bands.map((band) => ({
    type: 'rect',
    xref: 'x',
    yref: 'y',
    x0: xMin,
    x1: xMax,
    y0: band.from,
    y1: band.to,
    fillcolor: band.color,
    opacity: 0.28,
    line: {
      width: 0,
    },
    layer: 'below',
  }))
}

function buildProfileTickValues(bands) {
  const tickValues = []

  for (const band of bands) {
    tickValues.push(Number(band.from.toFixed(2)))
  }

  if (bands.length > 0) {
    tickValues.push(Number(bands[bands.length - 1].to.toFixed(2)))
  }

  return [...new Set(tickValues)]
}

async function renderHeatmap() {
  if (!grid.value) {
    return
  }

  await nextTick()

  if (!heatmapContainer.value) {
    return
  }

  const { min, max } = getZRange(grid.value.z)

  if (mapMode.value === 'profile') {
    const profile = buildProfileData(grid.value)
    const xMin = Math.min(...profile.x)
    const xMax = Math.max(...profile.x)
    const bands = rangeBands.value
    const baseline = profile.x.map(() => min)

    const data = [
      {
        x: profile.x,
        y: baseline,
        type: 'scatter',
        mode: 'lines',
        line: {
          color: 'rgba(0,0,0,0)',
        },
        hoverinfo: 'skip',
        showlegend: false,
      },
      {
        x: profile.x,
        y: profile.z,
        type: 'scatter',
        mode: 'lines',
        line: {
          color: '#111827',
          width: 2.5,
        },
        fill: 'tonexty',
        fillcolor: 'rgba(17, 24, 39, 0.18)',
        name: 'Terrain profile',
        hovertemplate: 'X: %{x:.2f}<br>Height: %{y:.2f}<extra></extra>',
      },
    ]

    const layout = {
      title: 'Side Elevation Profile',
      autosize: true,
      margin: {
        l: 70,
        r: 30,
        t: 60,
        b: 60,
      },
      xaxis: {
        title: 'Distance / X coordinate',
      },
      yaxis: {
        title: 'Height',
        tickmode: 'array',
        tickvals: buildProfileTickValues(bands),
      },
      shapes: buildProfileShapes(bands, xMin, xMax),
      showlegend: false,
    }

    const config = {
      responsive: true,
      displaylogo: false,
    }

    Plotly.react(heatmapContainer.value, data, layout, config)
    return
  }

  const isElevationMode = mapMode.value === 'elevation'

  const data = [
    {
      x: grid.value.x,
      y: grid.value.y,
      z: grid.value.z,
      type: 'heatmap',
      colorscale: isElevationMode ? createElevationColorscale() : 'Viridis',
      zsmooth: isElevationMode ? false : 'best',
      zmin: min,
      zmax: max,
      colorbar: {
        title: isElevationMode ? 'Elevation zones' : 'Height Z',
      },
    },
  ]

  const layout = {
    title: isElevationMode ? '2D Elevation Zone Map' : '2D Terrain Heatmap',
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

watch([grid, mapMode], renderHeatmap, {
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
    <div class="section-header">
      <div>
        <h2>2D-карта рельефа</h2>
        <p class="section-description">
          Переключайтесь между видом сверху, зонами высот и боковым профилем рельефа.
        </p>
      </div>

      <label class="mode-switcher">
        Режим карты:
        <select v-model="mapMode">
          <option value="smooth">Плавный градиент</option>
          <option value="elevation">Зоны высот</option>
          <option value="profile">Боковой профиль</option>
        </select>
      </label>
    </div>

    <div ref="heatmapContainer" class="heatmap-container"></div>

    <div v-if="mapMode === 'profile'" class="range-legend">
      <h3>Диапазоны высот</h3>

      <div class="range-items">
        <div
          v-for="band in rangeBands"
          :key="band.label"
          class="range-item"
        >
          <span
            class="range-color"
            :style="{ backgroundColor: band.color }"
          ></span>
          <span>{{ band.label }}</span>
        </div>
      </div>
    </div>
  </section>
</template>