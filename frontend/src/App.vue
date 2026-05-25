<script setup>
import FileUploader from './components/FileUploader.vue'
import StatsPanel from './components/StatsPanel.vue'
import Terrain3D from './components/Terrain3D.vue'
import Heatmap2D from './components/Heatmap2D.vue'
</script>

<template>
  <main class="app">
    <header class="header">
      <div>
        <p class="eyebrow">Платформа анализа рельефа</p>
        <h1>TerraScan</h1>
        <p>
          Загрузка XYZ-данных, построение 3D-модели рельефа на основе TIN,
          генерация тепловых карт и анализ высотных профилей местности.
        </p>
      </div>
    </header>

    <section class="upload-strip">
      <FileUploader />
    </section>

    <section class="terrain-layout">
      <section class="terrain-main">
        <Terrain3D />
      </section>

      <aside class="terrain-info-side">
        <StatsPanel />
      </aside>
    </section>

    <section class="wide-panel">
      <Heatmap2D />
    </section>
  </main>
</template>