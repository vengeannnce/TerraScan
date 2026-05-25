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

const grid = computed(() => {
  return terrainStore.processResult?.grid || null
})

const tin = computed(() => {
  return terrainStore.processResult?.tin || null
})

let scene = null
let camera = null
let renderer = null
let controls = null
let animationId = null
let resizeObserver = null

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

function createColorByHeight(value, zMin, zRange) {
  const normalizedHeight = (value - zMin) / zRange
  const color = new THREE.Color()

  color.setHSL(0.65 - normalizedHeight * 0.45, 0.8, 0.5)

  return color
}

function createGridGeometry(gridData) {
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

      positions[vertexOffset] = (dataX - xCenter) * xScale
      positions[vertexOffset + 1] = (dataZ - zMin) * zScale
      positions[vertexOffset + 2] = (dataY - yCenter) * yScale
      vertexOffset += 3

      const color = createColorByHeight(dataZ, zMin, zRange)

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
  geometry.computeBoundingBox()

  return geometry
}

function createTinGeometry(tinData) {
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
  const heightSize = 22

  const xScale = horizontalSize / xRange
  const yScale = horizontalSize / yRange
  const zScale = heightSize / zRange

  const xCenter = (xMin + xMax) / 2
  const yCenter = (yMin + yMax) / 2

  const positions = new Float32Array(vertices.length * 3)
  const colors = new Float32Array(vertices.length * 3)
  const indices = new Uint32Array(faces.length * 3)

  let vertexOffset = 0
  let colorOffset = 0

  for (let index = 0; index < vertices.length; index += 1) {
    const [dataX, dataY, dataZ] = vertices[index]

    positions[vertexOffset] = (dataX - xCenter) * xScale
    positions[vertexOffset + 1] = (dataZ - zMin) * zScale
    positions[vertexOffset + 2] = (dataY - yCenter) * yScale
    vertexOffset += 3

    const color = createColorByHeight(dataZ, zMin, zRange)

    colors[colorOffset] = color.r
    colors[colorOffset + 1] = color.g
    colors[colorOffset + 2] = color.b
    colorOffset += 3
  }

  let indexOffset = 0

  for (let index = 0; index < faces.length; index += 1) {
    indices[indexOffset] = faces[index][0]
    indices[indexOffset + 1] = faces[index][1]
    indices[indexOffset + 2] = faces[index][2]

    indexOffset += 3
  }

  const geometry = new THREE.BufferGeometry()

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setIndex(new THREE.BufferAttribute(indices, 1))
  geometry.computeVertexNormals()
  geometry.computeBoundingBox()

  return geometry
}

function addTerrainToScene(geometry) {
  if (renderMode.value === 'solid') {
    const material = new THREE.MeshStandardMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      roughness: 0.85,
      metalness: 0.05,
    })

    const terrainMesh = new THREE.Mesh(geometry, material)
    scene.add(terrainMesh)

    return
  }

  if (renderMode.value === 'transparent') {
    const transparentMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.14,
      side: THREE.DoubleSide,
      depthWrite: false,
      roughness: 1,
      metalness: 0,
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
  if (geometrySource.value === 'tin' && tin.value) {
    return createTinGeometry(tin.value)
  }

  if (grid.value) {
    const terrainGrid = downsampleGrid(grid.value, meshDetail.value)
    return createGridGeometry(terrainGrid)
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

  const geometry = buildGeometry()

  if (!geometry) {
    return
  }

  addTerrainToScene(geometry)

  const ambientLight = new THREE.AmbientLight(0xffffff, 1.2)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 2)
  directionalLight.position.set(80, 120, 80)
  scene.add(directionalLight)

  const gridHelper = new THREE.GridHelper(140, 14)
  scene.add(gridHelper)

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

watch([grid, tin, geometrySource, renderMode, meshDetail], renderTerrain, {
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

    <div ref="terrainContainer" class="terrain-container"></div>
  </section>
</template>