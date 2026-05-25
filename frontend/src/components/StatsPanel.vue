<script setup>
import { computed } from 'vue'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()

const result = computed(() => {
  return terrainStore.processResult || terrainStore.uploadResult
})

const stats = computed(() => {
  return result.value?.stats || null
})

const tin = computed(() => {
  return terrainStore.processResult?.tin || null
})
</script>

<template>
  <section v-if="result" class="card">
    <h2>Информация о рельефе</h2>

    <div class="stats-grid">
      <div>
        <span>Файл</span>
        <strong>{{ result.filename }}</strong>
      </div>

      <div>
        <span>Точек</span>
        <strong>{{ result.points_count }}</strong>
      </div>

      <div v-if="result.grid_size">
        <span>2D-сетка</span>
        <strong>{{ result.grid_size }} × {{ result.grid_size }}</strong>
      </div>

      <div v-if="tin">
        <span>TIN-вершины</span>
        <strong>{{ tin.mesh_points_count }}</strong>
      </div>

      <div v-if="tin">
        <span>TIN-треугольники</span>
        <strong>{{ tin.triangles_count }}</strong>
      </div>

      <div v-if="stats">
        <span>Диапазон X</span>
        <strong>{{ stats.x_min }} — {{ stats.x_max }}</strong>
      </div>

      <div v-if="stats">
        <span>Диапазон Y</span>
        <strong>{{ stats.y_min }} — {{ stats.y_max }}</strong>
      </div>

      <div v-if="stats">
        <span>Диапазон высот</span>
        <strong>{{ stats.z_min }} — {{ stats.z_max }}</strong>
      </div>

      <div v-if="stats">
        <span>Средняя высота</span>
        <strong>{{ stats.z_mean }}</strong>
      </div>
    </div>
  </section>
</template>