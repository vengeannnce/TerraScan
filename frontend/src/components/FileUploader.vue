<script setup>
import { ref } from 'vue'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()
const gridSize = ref(30)

function handleFileChange(event) {
  const file = event.target.files[0]

  if (file) {
    terrainStore.setSelectedFile(file)
  }
}
</script>

<template>
  <section class="card">
    <h2>Upload XYZ file</h2>

    <input
      type="file"
      accept=".csv,.txt"
      @change="handleFileChange"
    />

    <div v-if="terrainStore.selectedFile" class="file-info">
      Selected file: <strong>{{ terrainStore.selectedFile.name }}</strong>
    </div>

    <div class="controls">
      <label>
        Grid size:
        <input
          v-model.number="gridSize"
          type="number"
          min="5"
          max="300"
        />
      </label>
    </div>

    <div class="buttons">
      <button
        :disabled="terrainStore.loading || !terrainStore.selectedFile"
        @click="terrainStore.uploadFile"
      >
        Upload only
      </button>

      <button
        :disabled="terrainStore.loading || !terrainStore.selectedFile"
        @click="terrainStore.processFile(gridSize)"
      >
        Process terrain
      </button>
    </div>

    <p v-if="terrainStore.loading">Loading...</p>

    <p v-if="terrainStore.error" class="error">
      {{ terrainStore.error }}
    </p>
  </section>
</template>