<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

import { useTerrainStore } from '../stores/terrainStore'

const terrainStore = useTerrainStore()
const terrainContainer = ref(null)

const geometrySource = ref('tin')
const renderMode = ref('solid')
const meshDetail = ref(300)
const heightCutoffPercent = ref(100)

const grid = computed(() => {
  return terrainStore.processResult?.grid || null
})

const tin = computed(() => {
  return terrainStore.processResult?.tin || null
})

const activeZRange = computed(() => {
  if (geometrySource.value === 'tin' && tin.value) {
    return getZRangeFromVertices(tin.value.vertices)
  }

  if (grid.value) {
    return getZRangeFromGrid(grid.value.z)
  }

  return null
})

const currentHeightCutoff = computed(() => {
  if (!activeZRange.value) {
    return null
  }

  const { zMin, zMax } = activeZRange.value

  return zMin + ((zMax - zMin) * heightCutoffPercent.value) / 100
})

const currentHeightCutoffLabel = computed(() => {
  if (currentHeightCutoff.value === null) {
    return '—'
  }

  return Number(currentHeightCutoff.value).toFixed(2)
})

let scene = null
let camera = null
let renderer = null
let controls = null
let animationId = null
let resizeObserver = null

function formatNumber(value) {
  return Number(value).toFixed(2)
}

function getBaseFilename() {
  const filename = terrainStore.processResult?.filename || 'terrain'

  return filename
    .replace(/\.[^/.]+$/, '')
    .replace(/[^a-zA-Z0-9а-яА-Я_-]/g, '_')
}

function downloadTextFile(content, filename, mimeType) {
  const blob = new Blob([content], {
    type: `${mimeType};charset=utf-8`,
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  link.click()

  URL.revokeObjectURL(url)
}

function export3dPng() {
  if (!renderer || !scene || !camera) {
    return
  }

  renderer.render(scene, camera)

  const imageUrl = renderer.domElement.toDataURL('image/png')
  const link = document.createElement('a')

  link.href = imageUrl
  link.download = `${getBaseFilename()}_3d_terrain.png`
  link.click()
}

function exportTinObj() {
  if (!tin.value) {
    return
  }

  const { vertices, faces } = tin.value
  const lines = []

  lines.push('# TerraScan TIN OBJ export')
  lines.push(`# Source file: ${terrainStore.processResult?.filename || 'terrain'}`)
  lines.push(`# Vertices: ${vertices.length}`)
  lines.push(`# Faces: ${faces.length}`)

  for (const vertex of vertices) {
    const [x, y, z] = vertex

    // OBJ uses Y as vertical axis, so we write x z y
    lines.push(`v ${x} ${z} ${y}`)
  }

  for (const face of faces) {
    const [a, b, c] = face

    // OBJ indices start from 1
    lines.push(`f ${a + 1} ${b + 1} ${c + 1}`)
  }

  downloadTextFile(
    lines.join('\n'),
    `${getBaseFilename()}_tin_model.obj`,
    'text/plain',
  )
}

function downsampleGrid(gridData, targetSize) {
  const sourceXSize = gridData.x.length
  const sourceYSize = gridData.y.length

  if (!targetSize || targetSize >= sourceXSize || targetSize >= sourceYSize) {
    return gridData
  }

  const xIndices = []
  const yIndices = []

  for (let index = 0; index < targetSize; index += 1) {
    const xIndex = Math.round((index / (targetSize - 1)) * (sourceXSize - 1))
    const yIndex = Math.round((index / (targetSize - 1)) * (sourceYSize - 1))

    xIndices.push(xIndex)
    yIndices.push(yIndex)
  }

  const sampledX = xIndices.map((index) => gridData.x[index])
  const sampledY = yIndices.map((index) => gridData.y[index])

  const sampledZ = yIndices.map((rowIndex) => {
    return xIndices.map((colIndex) => gridData.z[rowIndex][colIndex])
  })

  return {
    x: sampledX,
    y: sampledY,
    z: sampledZ,
  }
}

function getZRangeFromGrid(zMatrix) {
  let zMin = Infinity
  let zMax = -Infinity

  for (let row = 0; row < zMatrix.length; row += 1) {
    for (let col = 0; col < zMatrix[row].length; col += 1) {
      const value = zMatrix[row][col]

      if (value < zMin) zMin = value
      if (value > zMax) zMax = value
    }
  }

  return { zMin, zMax }
}

function getZRangeFromVertices(vertices) {
  let zMin = Infinity
  let zMax = -Infinity

  for (let index = 0; index < vertices.length; index += 1) {
    const value = vertices[index][2]

    if (value < zMin) zMin = value
    if (value > zMax) zMax = value
  }

  return { zMin, zMax }
}

function hexToRgb(hex) {
  const cleanHex = hex.replace('#', '')
  const bigint = Number.parseInt(cleanHex, 16)

  return {
    r: ((bigint >> 16) & 255) / 255,
    g: ((bigint >> 8) & 255) / 255,
    b: (bigint & 255) / 255,
  }
}

function interpolateColor(colorA, colorB, factor) {
  return {
    r: colorA.r + (colorB.r - colorA.r) * factor,
    g: colorA.g + (colorB.g - colorA.g) * factor,
    b: colorA.b + (colorB.b - colorA.b) * factor,
  }
}

function createTerrainColor(value, zMin, zRange) {
  const normalized = zRange === 0 ? 0 : (value - zMin) / zRange

  const colorStops = [
    { stop: 0.0, color: '#3455B5' },
    { stop: 0.22, color: '#6F92D6' },
    { stop: 0.5, color: '#D4CDC4' },
    { stop: 0.78, color: '#C97A57' },
    { stop: 1.0, color: '#B32020' },
  ]

  for (let index = 0; index < colorStops.length - 1; index += 1) {
    const current = colorStops[index]
    const next = colorStops[index + 1]

    if (normalized >= current.stop && normalized <= next.stop) {
      const localFactor =
        (normalized - current.stop) / (next.stop - current.stop)

      const rgb = interpolateColor(
        hexToRgb(current.color),
        hexToRgb(next.color),
        localFactor,
      )

      return new THREE.Color(rgb.r, rgb.g, rgb.b)
    }
  }

  const lastColor = hexToRgb(colorStops[colorStops.length - 1].color)

  return new THREE.Color(lastColor.r, lastColor.g, lastColor.b)
}

function createGridGeometry(gridData, maxHeight = Infinity) {
  const xValues = gridData.x
  const yValues = gridData.y
  const zMatrix = gridData.z

  const rows = yValues.length
  const cols = xValues.length

  const xMin = Math.min(...xValues)
  const xMax = Math.max(...xValues)
  const yMin = Math.min(...yValues)
  const yMax = Math.max(...yValues)

  const { zMin, zMax } = getZRangeFromGrid(zMatrix)

  const xRange = xMax - xMin || 1
  const yRange = yMax - yMin || 1
  const zRange = zMax - zMin || 1

  const horizontalSize = 120
  const heightSize = 26

  const xScale = horizontalSize / xRange
  const yScale = horizontalSize / yRange
  const zScale = heightSize / zRange

  const xCenter = (xMin + xMax) / 2
  const yCenter = (yMin + yMax) / 2

  const vertexCount = rows * cols

  const positions = new Float32Array(vertexCount * 3)
  const colors = new Float32Array(vertexCount * 3)
  const sourceHeights = new Float32Array(vertexCount)
  const indices = []

  let vertexOffset = 0
  let colorOffset = 0

  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      const dataX = xValues[col]
      const dataY = yValues[row]
      const dataZ = zMatrix[row][col]
      const vertexIndex = row * cols + col

      positions[vertexOffset] = (dataX - xCenter) * xScale
      positions[vertexOffset + 1] = (dataZ - zMin) * zScale
      positions[vertexOffset + 2] = (dataY - yCenter) * yScale
      vertexOffset += 3

      sourceHeights[vertexIndex] = dataZ

      const color = createTerrainColor(dataZ, zMin, zRange)

      colors[colorOffset] = color.r
      colors[colorOffset + 1] = color.g
      colors[colorOffset + 2] = color.b
      colorOffset += 3
    }
  }

  for (let row = 0; row < rows - 1; row += 1) {
    for (let col = 0; col < cols - 1; col += 1) {
      const topLeft = row * cols + col
      const topRight = topLeft + 1
      const bottomLeft = (row + 1) * cols + col
      const bottomRight = bottomLeft + 1

      if (
        sourceHeights[topLeft] <= maxHeight &&
        sourceHeights[bottomLeft] <= maxHeight &&
        sourceHeights[topRight] <= maxHeight
      ) {
        indices.push(topLeft, bottomLeft, topRight)
      }

      if (
        sourceHeights[topRight] <= maxHeight &&
        sourceHeights[bottomLeft] <= maxHeight &&
        sourceHeights[bottomRight] <= maxHeight
      ) {
        indices.push(topRight, bottomLeft, bottomRight)
      }
    }
  }

  const geometry = new THREE.BufferGeometry()

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setIndex(indices)
  geometry.computeVertexNormals()
  geometry.computeBoundingBox()

  return geometry
}

function createTinGeometry(tinData, maxHeight = Infinity) {
  const vertices = tinData.vertices
  const faces = tinData.faces

  const xValues = vertices.map((vertex) => vertex[0])
  const yValues = vertices.map((vertex) => vertex[1])

  const xMin = Math.min(...xValues)
  const xMax = Math.max(...xValues)
  const yMin = Math.min(...yValues)
  const yMax = Math.max(...yValues)

  const { zMin, zMax } = getZRangeFromVertices(vertices)

  const xRange = xMax - xMin || 1
  const yRange = yMax - yMin || 1
  const zRange = zMax - zMin || 1

  const horizontalSize = 120
  const heightSize = 26

  const xScale = horizontalSize / xRange
  const yScale = horizontalSize / yRange
  const zScale = heightSize / zRange

  const xCenter = (xMin + xMax) / 2
  const yCenter = (yMin + yMax) / 2

  const positions = new Float32Array(vertices.length * 3)
  const colors = new Float32Array(vertices.length * 3)
  const sourceHeights = new Float32Array(vertices.length)
  const indices = []

  let vertexOffset = 0
  let colorOffset = 0

  for (let index = 0; index < vertices.length; index += 1) {
    const [dataX, dataY, dataZ] = vertices[index]

    positions[vertexOffset] = (dataX - xCenter) * xScale
    positions[vertexOffset + 1] = (dataZ - zMin) * zScale
    positions[vertexOffset + 2] = (dataY - yCenter) * yScale
    vertexOffset += 3

    sourceHeights[index] = dataZ

    const color = createTerrainColor(dataZ, zMin, zRange)

    colors[colorOffset] = color.r
    colors[colorOffset + 1] = color.g
    colors[colorOffset + 2] = color.b
    colorOffset += 3
  }

  for (let index = 0; index < faces.length; index += 1) {
    const a = faces[index][0]
    const b = faces[index][1]
    const c = faces[index][2]

    if (
      sourceHeights[a] <= maxHeight &&
      sourceHeights[b] <= maxHeight &&
      sourceHeights[c] <= maxHeight
    ) {
      indices.push(a, b, c)
    }
  }

  const geometry = new THREE.BufferGeometry()

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setIndex(indices)
  geometry.computeVertexNormals()
  geometry.computeBoundingBox()

  return geometry
}

function addTerrainToScene(geometry) {
  if (renderMode.value === 'solid') {
    const material = new THREE.MeshPhongMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      shininess: 10,
      flatShading: false,
    })

    const terrainMesh = new THREE.Mesh(geometry, material)
    scene.add(terrainMesh)

    return
  }

  if (renderMode.value === 'transparent') {
    const transparentMaterial = new THREE.MeshPhongMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.18,
      side: THREE.DoubleSide,
      shininess: 6,
      flatShading: false,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: 1,
      polygonOffsetUnits: 1,
    })

    const transparentMesh = new THREE.Mesh(geometry, transparentMaterial)
    scene.add(transparentMesh)

    const wireframeMaterial = new THREE.MeshBasicMaterial({
      vertexColors: true,
      wireframe: true,
      transparent: true,
      opacity: 0.95,
    })

    const wireframeMesh = new THREE.Mesh(geometry, wireframeMaterial)
    scene.add(wireframeMesh)

    return
  }

  if (renderMode.value === 'wireframe') {
    const wireframeMaterial = new THREE.MeshBasicMaterial({
      vertexColors: true,
      wireframe: true,
      transparent: true,
      opacity: 1,
    })

    const wireframeMesh = new THREE.Mesh(geometry, wireframeMaterial)
    scene.add(wireframeMesh)
  }
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

  const disposedGeometries = new Set()
  const disposedMaterials = new Set()

  if (scene) {
    scene.traverse((object) => {
      if (object.geometry && !disposedGeometries.has(object.geometry)) {
        object.geometry.dispose()
        disposedGeometries.add(object.geometry)
      }

      if (object.material) {
        const materials = Array.isArray(object.material)
          ? object.material
          : [object.material]

        materials.forEach((material) => {
          if (!disposedMaterials.has(material)) {
            material.dispose()
            disposedMaterials.add(material)
          }
        })
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

function buildGeometry() {
  const maxHeight = currentHeightCutoff.value ?? Infinity

  if (geometrySource.value === 'tin' && tin.value) {
    return createTinGeometry(tin.value, maxHeight)
  }

  if (grid.value) {
    const terrainGrid = downsampleGrid(grid.value, meshDetail.value)

    return createGridGeometry(terrainGrid, maxHeight)
  }

  return null
}

async function renderTerrain() {
  if (!grid.value && !tin.value) {
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
  scene.background = new THREE.Color(0xf1f1f1)

  camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 10000)

  renderer = new THREE.WebGLRenderer({
    antialias: true,
    powerPreference: 'high-performance',
    preserveDrawingBuffer: true,
  })

  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(width, height)

  terrainContainer.value.innerHTML = ''
  terrainContainer.value.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.maxPolarAngle = Math.PI / 2.02
  controls.minDistance = 20
  controls.maxDistance = 500

  const geometry = buildGeometry()

  if (!geometry || !geometry.boundingBox) {
    return
  }

  addTerrainToScene(geometry)

  const ambientLight = new THREE.AmbientLight(0xffffff, 1.15)
  scene.add(ambientLight)

  const hemiLight = new THREE.HemisphereLight(0xffffff, 0xd9d9d9, 0.65)
  scene.add(hemiLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 1.35)
  directionalLight.position.set(90, 120, 100)
  scene.add(directionalLight)

  const fillLight = new THREE.DirectionalLight(0xffffff, 0.65)
  fillLight.position.set(-70, 90, -70)
  scene.add(fillLight)

  const gridHelper = new THREE.GridHelper(145, 14, 0xb0b0b0, 0xcfcfcf)
  gridHelper.position.y = 0
  scene.add(gridHelper)

  const box = geometry.boundingBox
  const center = new THREE.Vector3()
  const size = new THREE.Vector3()

  box.getCenter(center)
  box.getSize(size)

  const maxSize = Math.max(size.x, size.y, size.z, 1)

  camera.position.set(
    center.x - maxSize * 0.18,
    center.y + maxSize * 0.72,
    center.z + maxSize * 1.12,
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

watch([grid, tin, geometrySource, renderMode, meshDetail, heightCutoffPercent], renderTerrain, {
  deep: true,
  flush: 'post',
})

onBeforeUnmount(() => {
  disposeScene()
})
</script>

<template>
  <section v-if="grid || tin" class="card">
    <div class="section-header">
      <div>
        <h2>3D-рельеф</h2>
        <p class="section-description">
          TIN использует реальные XYZ-точки для детальной 3D-модели.
          Сеточная модель доступна как альтернативный режим.
        </p>
      </div>

      <div class="mode-controls">
        <label class="mode-switcher">
          Источник 3D:
          <select v-model="geometrySource">
            <option value="tin">TIN-модель</option>
            <option value="grid">Сеточная модель</option>
          </select>
        </label>

        <label class="mode-switcher">
          Режим 3D:
          <select v-model="renderMode">
            <option value="solid">Сплошная поверхность</option>
            <option value="transparent">Прозрачный контур</option>
            <option value="wireframe">Только каркас</option>
          </select>
        </label>

        <label
          v-if="geometrySource === 'grid'"
          class="mode-switcher"
        >
          Детализация сетки:
          <select v-model.number="meshDetail">
            <option :value="100">100 × 100</option>
            <option :value="200">200 × 200</option>
            <option :value="300">300 × 300</option>
            <option :value="500">500 × 500</option>
            <option :value="700">700 × 700</option>
            <option :value="1000">1000 × 1000</option>
            <option :value="1500">1500 × 1500</option>
            <option :value="2000">Полная / 2000 × 2000</option>
          </select>
        </label>

        <button
          type="button"
          class="secondary-action-button"
          @click="export3dPng"
        >
          Export 3D PNG
        </button>

        <button
          type="button"
          class="secondary-action-button"
          :disabled="!tin"
          @click="exportTinObj"
        >
          Export TIN OBJ
        </button>
      </div>
    </div>

    <div class="terrain-toolbar">
      <div class="height-filter-panel">
        <div class="height-filter-header">
          <span>Фильтр по высоте</span>
          <strong v-if="activeZRange">
            Показывать до: {{ currentHeightCutoffLabel }}
          </strong>
        </div>

        <input
          v-model.number="heightCutoffPercent"
          type="range"
          min="0"
          max="100"
          step="1"
        />

        <div v-if="activeZRange" class="height-filter-scale">
          <span>Мин: {{ formatNumber(activeZRange.zMin) }}</span>
          <span>Макс: {{ formatNumber(activeZRange.zMax) }}</span>
        </div>
      </div>
    </div>

    <div
      v-if="tin && geometrySource === 'tin'"
      class="tin-info"
    >
      TIN-модель:
      <strong>{{ tin.mesh_points_count }}</strong> вершин,
      <strong>{{ tin.triangles_count }}</strong> треугольников
    </div>

    <div ref="terrainContainer" class="terrain-container terrain-container-light"></div>
  </section>
</template>