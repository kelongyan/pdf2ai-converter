const API_BASE = "/api"

export async function uploadFile(file: File) {
  const form = new FormData()
  form.append("file", file)
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<{ file_id: string; file_name: string; size: number }>
}

export async function startConvert(params: {
  file_id: string
  output_format: string
  mode: string
  resume: boolean
}) {
  const res = await fetch(`${API_BASE}/convert`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getTasks() {
  const res = await fetch(`${API_BASE}/tasks`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getTask(id: string) {
  const res = await fetch(`${API_BASE}/tasks/${id}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function deleteTask(id: string) {
  const res = await fetch(`${API_BASE}/tasks/${id}`, { method: "DELETE" })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function getDownloadUrl(id: string) {
  return `${API_BASE}/tasks/${id}/download`
}

export async function getPreview(id: string) {
  const res = await fetch(`${API_BASE}/tasks/${id}/preview`)
  if (!res.ok) throw new Error(await res.text())
  return res.json() as Promise<{ content: string }>
}

export async function getProfiles() {
  const res = await fetch(`${API_BASE}/config/profiles`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function createProfile(data: {
  name: string
  api_url: string
  api_key: string
  model: string
  dpi: number
  chunk_size: number
}) {
  const res = await fetch(`${API_BASE}/config/profiles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function deleteProfile(name: string) {
  const res = await fetch(`${API_BASE}/config/profiles/${name}`, { method: "DELETE" })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
