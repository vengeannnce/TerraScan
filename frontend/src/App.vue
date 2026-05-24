<script setup>
import FileUploader from './components/FileUploader.vue'
import StatsPanel from './components/StatsPanel.vue'
import Terrain3D from './components/Terrain3D.vue'
import Heatmap2D from './components/Heatmap2D.vue'
</script>

<template>
  <main class="app">
    <header class="header">
      <h1>TerraScan</h1>
      <p>XYZ terrain processing and visualization platform</p>
    </header>

    <FileUploader />
    <StatsPanel />
    <Terrain3D />
    <Heatmap2D />
  </main>
</template>