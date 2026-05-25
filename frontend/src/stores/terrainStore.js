import { defineStore } from 'pinia'

import { uploadTerrainFile, processTerrainFile } from '../services/apiService'

export const useTerrainStore = defineStore('terrain', {
  state: () => ({
    selectedFile: null,
    uploadResult: null,
    processResult: null,
    loading: false,
    error: null,
  }),

  actions: {
    setSelectedFile(file) {
      this.selectedFile = file
      this.uploadResult = null
      this.processResult = null
      this.error = null
    },

    async uploadFile() {
      if (!this.selectedFile) {
        this.error = 'Choose a file first'
        return
      }

      this.loading = true
      this.error = null

      try {
        this.uploadResult = await uploadTerrainFile(this.selectedFile)
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async processFile(gridSize = 250, tinMaxPoints = 50000) {
      if (!this.selectedFile) {
        this.error = 'Choose a file first'
        return
      }

      this.loading = true
      this.error = null

      try {
        this.processResult = await processTerrainFile(
          this.selectedFile,
          gridSize,
          tinMaxPoints,
        )
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
  },
})