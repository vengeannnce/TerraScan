<script setup>
import { computed } from 'vue'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()

const result = computed(() => {
  return terrainStore.processResult || terrainStore.uploadResult
})
</script>

<template>
  <section v-if="result" class="card">
    <h2>Backend JSON response</h2>

    <pre>{{ JSON.stringify(result, null, 2) }}</pre>
  </section>
</template>