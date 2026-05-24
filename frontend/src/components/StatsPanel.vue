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
</script>

<template>
  <section v-if="result" class="card">
    <h2>Terrain information</h2>

    <div class="stats-grid">
      <div>
        <span>Filename</span>
        <strong>{{ result.filename }}</strong>
      </div>

      <div>
        <span>Points</span>
        <strong>{{ result.points_count }}</strong>
      </div>

      <div v-if="result.grid_size">
        <span>Grid size</span>
        <strong>{{ result.grid_size }} x {{ result.grid_size }}</strong>
      </div>

      <div v-if="stats">
        <span>X range</span>
        <strong>{{ stats.x_min }} — {{ stats.x_max }}</strong>
      </div>

      <div v-if="stats">
        <span>Y range</span>
        <strong>{{ stats.y_min }} — {{ stats.y_max }}</strong>
      </div>

      <div v-if="stats">
        <span>Z range</span>
        <strong>{{ stats.z_min }} — {{ stats.z_max }}</strong>
      </div>

      <div v-if="stats">
        <span>Average Z</span>
        <strong>{{ stats.z_mean }}</strong>
      </div>
    </div>
  </section>
</template>