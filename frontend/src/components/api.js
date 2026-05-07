const API = 'http://localhost:8000/api'

export async function gradeSubmission(file, githubUrl) {
  const form = new FormData()
  form.append('file', file)
  form.append('github_url', githubUrl)
  const res = await fetch(`${API}/grade`, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Failed to start grading')
  return res.json()
}

export async function parseProblem(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}/parse-problem`, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Failed to parse problem statement')
  return res.json()
}

export async function getSubmissions() {
  const res = await fetch(`${API}/submissions`)
  if (!res.ok) return []
  return res.json()
}

export async function getSubmission(id) {
  const res = await fetch(`${API}/submissions/${id}`)
  if (!res.ok) throw new Error('Submission not found')
  return res.json()
}

export async function getStatus(id) {
  const res = await fetch(`${API}/submissions/${id}/status`)
  if (!res.ok) throw new Error('Status unavailable')
  return res.json()
}

export async function deleteSubmission(id) {
  const res = await fetch(`${API}/submissions/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Delete failed')
  return res.json()
}
