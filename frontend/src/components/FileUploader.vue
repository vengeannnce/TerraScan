<script setup>
import { ref } from 'vue'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()

const fileInput = ref(null)
const gridSize = ref(250)
const tinMaxPoints = ref(50000)

function openFileDialog() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  const file = event.target.files[0]

  if (file) {
    terrainStore.setSelectedFile(file)
  }
}
</script>

<template>
  <section class="card upload-card">
    <div class="upload-card-header">
      <h2>Загрузка XYZ-файла</h2>
      <p class="section-description">
        Выберите файл с координатами рельефа и настройте параметры построения 2D и 3D-модели.
      </p>
    </div>

    <div class="upload-card-body">
      <div class="upload-field file-upload-field">
        <label>Исходный файл</label>

        <input
          ref="fileInput"
          class="native-file-input"
          type="file"
          accept=".csv,.txt"
          @change="handleFileChange"
        />

        <button
          type="button"
          class="file-picker-button"
          @click="openFileDialog"
        >
          Choose file
        </button>

        <div v-if="terrainStore.selectedFile" class="file-info">
          Выбран файл: <strong>{{ terrainStore.selectedFile.name }}</strong>
        </div>

        <div v-else class="file-info muted">
          Файл не выбран
        </div>
      </div>

      <div class="upload-field">
        <label>
          Сетка для 2D
          <input
            v-model.number="gridSize"
            type="number"
            min="5"
            max="2000"
          />
        </label>

        <p class="hint">
          Используется для тепловой карты. Рекомендуется: 250–700.
        </p>
      </div>

      <div class="upload-field">
        <label>
          Точки TIN для 3D
          <input
            v-model.number="tinMaxPoints"
            type="number"
            min="100"
            max="250000"
            step="1000"
          />
        </label>

        <p class="hint">
          Используется для 3D-модели. Рекомендуется: 50 000–150 000.
        </p>
      </div>
    </div>

    <div class="upload-actions">
      <button
        :disabled="terrainStore.loading || !terrainStore.selectedFile"
        @click="terrainStore.uploadFile"
      >
        Upload
      </button>

      <button
        :disabled="terrainStore.loading || !terrainStore.selectedFile"
        @click="terrainStore.processFile(gridSize, tinMaxPoints)"
      >
        Process
      </button>
    </div>

    <p v-if="terrainStore.loading" class="loading-text">
      Обработка данных рельефа...
    </p>

    <p v-if="terrainStore.error" class="error">
      {{ terrainStore.error }}
    </p>
  </section>
</template>