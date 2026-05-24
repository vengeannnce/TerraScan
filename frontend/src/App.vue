<script setup>
import FileUploader from './components/FileUploader.vue'
import StatsPanel from './components/StatsPanel.vue'
import Heatmap2D from './components/Heatmap2D.vue'
import JsonPreview from './components/JsonPreview.vue'
</script>

<template>
  <main class="app">
    <header class="header">
      <h1>TerraScan</h1>
      <p>XYZ terrain processing and visualization platform</p>
    </header>

    <FileUploader />
    <StatsPanel />
    <Heatmap2D />
    <JsonPreview />
  </main>
</template>