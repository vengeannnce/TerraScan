const API_BASE_URL = 'http://127.0.0.1:8000/api'

async function handleResponse(response) {
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || 'Request failed')
  }

  return data
}

export async function uploadTerrainFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/upload/`, {
    method: 'POST',
    body: formData,
  })

  return handleResponse(response)
}

export async function processTerrainFile(file, gridSize = 50) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('grid_size', gridSize)

  const response = await fetch(`${API_BASE_URL}/process/`, {
    method: 'POST',
    body: formData,
  })

  return handleResponse(response)
}