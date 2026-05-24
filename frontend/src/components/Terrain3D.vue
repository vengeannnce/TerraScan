<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()
const terrainContainer = ref(null)

const grid = computed(() => {
  return terrainStore.processResult?.grid || null
})

let scene = null
let camera = null
let renderer = null
let controls = null
let animationId = null
let resizeObserver = null

function createTerrainGeometry(gridData) {
  const xValues = gridData.x
  const yValues = gridData.y
  const zMatrix = gridData.z

  const rows = yValues.length
  const cols = xValues.length

  const xMin = Math.min(...xValues)
  const xMax = Math.max(...xValues)
  const yMin = Math.min(...yValues)
  const yMax = Math.max(...yValues)

  let zMin = Infinity
  let zMax = -Infinity

  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const value = zMatrix[row][col]
      if (value < zMin) zMin = value
      if (value > zMax) zMax = value
    }
  }

  const xRange = xMax - xMin || 1
  const yRange = yMax - yMin || 1
  const zRange = zMax - zMin || 1

  const horizontalSize = 120
  const heightSize = 22

  const xScale = horizontalSize / xRange
  const yScale = horizontalSize / yRange
  const zScale = heightSize / zRange

  const xCenter = (xMin + xMax) / 2
  const yCenter = (yMin + yMax) / 2

  const vertexCount = rows * cols
  const indexCount = (rows - 1) * (cols - 1) * 6

  const positions = new Float32Array(vertexCount * 3)
  const colors = new Float32Array(vertexCount * 3)
  const indices = new Uint32Array(indexCount)

  let vertexOffset = 0
  let colorOffset = 0

  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const dataX = xValues[col]
      const dataY = yValues[row]
      const dataZ = zMatrix[row][col]

      const sceneX = (dataX - xCenter) * xScale
      const sceneY = (dataZ - zMin) * zScale
      const sceneZ = (dataY - yCenter) * yScale

      positions[vertexOffset] = sceneX
      positions[vertexOffset + 1] = sceneY
      positions[vertexOffset + 2] = sceneZ
      vertexOffset += 3

      const normalizedHeight = (dataZ - zMin) / zRange
      const color = new THREE.Color()
      color.setHSL(0.65 - normalizedHeight * 0.45, 0.8, 0.5)

      colors[colorOffset] = color.r
      colors[colorOffset + 1] = color.g
      colors[colorOffset + 2] = color.b
      colorOffset += 3
    }
  }

  let indexOffset = 0

  for (let row = 0; row < rows - 1; row += 1) {
    for (let col = 0; col < cols - 1; col += 1) {
      const topLeft = row * cols + col
      const topRight = topLeft + 1
      const bottomLeft = (row + 1) * cols + col
      const bottomRight = bottomLeft + 1

      indices[indexOffset] = topLeft
      indices[indexOffset + 1] = bottomLeft
      indices[indexOffset + 2] = topRight

      indices[indexOffset + 3] = topRight
      indices[indexOffset + 4] = bottomLeft
      indices[indexOffset + 5] = bottomRight

      indexOffset += 6
    }
  }

  const geometry = new THREE.BufferGeometry()

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setIndex(new THREE.BufferAttribute(indices, 1))
  geometry.computeVertexNormals()

  return geometry
}

function disposeScene() {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }

  if (resizeObserver) {
    resizeObserver.disconnect()
  }

  if (controls) {
    controls.dispose()
  }

  if (scene) {
    scene.traverse((object) => {
      if (object.geometry) {
        object.geometry.dispose()
      }

      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach((material) => material.dispose())
        } else {
          object.material.dispose()
        }
      }
    })
  }

  if (renderer) {
    renderer.dispose()

    if (renderer.domElement?.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
  }

  scene = null
  camera = null
  renderer = null
  controls = null
  animationId = null
  resizeObserver = null
}

async function renderTerrain() {
  if (!grid.value) {
    return
  }

  await nextTick()

  if (!terrainContainer.value) {
    return
  }

  disposeScene()

  const width = terrainContainer.value.clientWidth
  const height = terrainContainer.value.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf8fafc)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000)

  renderer = new THREE.WebGLRenderer({
  antialias: false,
  powerPreference: 'high-performance',
})
  renderer.setPixelRatio(1)
  renderer.setSize(width, height)

  terrainContainer.value.innerHTML = ''
  terrainContainer.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true

  const geometry = createTerrainGeometry(grid.value)

  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,
    side: THREE.DoubleSide,
    roughness: 0.85,
    metalness: 0.05,
  })

  const terrainMesh = new THREE.Mesh(geometry, material)
  scene.add(terrainMesh)

  const ambientLight = new THREE.AmbientLight(0xffffff, 1.2)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 2)
  directionalLight.position.set(80, 120, 80)
  scene.add(directionalLight)

  const gridHelper = new THREE.GridHelper(140, 14)
  scene.add(gridHelper)

  const axesHelper = new THREE.AxesHelper(80)
  scene.add(axesHelper)

  geometry.computeBoundingBox()

  const box = geometry.boundingBox
  const center = new THREE.Vector3()
  const size = new THREE.Vector3()

  box.getCenter(center)
  box.getSize(size)

  const maxSize = Math.max(size.x, size.y, size.z, 1)

  camera.position.set(
    center.x + maxSize * 0.8,
    center.y + maxSize * 0.7,
    center.z + maxSize * 0.9,
  )

  controls.target.copy(center)
  controls.update()

  resizeObserver = new ResizeObserver(() => {
    if (!terrainContainer.value || !camera || !renderer) {
      return
    }

    const newWidth = terrainContainer.value.clientWidth
    const newHeight = terrainContainer.value.clientHeight

    camera.aspect = newWidth / newHeight
    camera.updateProjectionMatrix()
    renderer.setSize(newWidth, newHeight)
  })

  resizeObserver.observe(terrainContainer.value)

  function animate() {
    animationId = requestAnimationFrame(animate)

    controls.update()
    renderer.render(scene, camera)
  }

  animate()
}

watch(grid, renderTerrain, {
  deep: true,
  flush: 'post',
})

onBeforeUnmount(() => {
  disposeScene()
})
</script>

<template>
  <section v-if="grid" class="card">
    <h2>3D Terrain</h2>
    <div ref="terrainContainer" class="terrain-container"></div>
  </section>
</template>