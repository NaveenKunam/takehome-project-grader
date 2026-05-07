import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ProgressTracker from '../components/ProgressTracker'
import RequirementsPreview from '../components/RequirementsPreview'
import SubmissionsTable from '../components/SubmissionsTable'
import UploadForm from '../components/UploadForm'
import { getStatus, getSubmission, getSubmissions, gradeSubmission, parseProblem } from '../components/api'

export default function Home() {
  const [file, setFile] = useState(null)
  const [githubUrl, setGithubUrl] = useState('')
  const [submissions, setSubmissions] = useState([])
  const [currentId, setCurrentId] = useState(null)
  const [stepLabel, setStepLabel] = useState('')
  const [requirements, setRequirements] = useState(null)
  const [parsing, setParsing] = useState(false)
  const navigate = useNavigate()

  async function refresh() {
    setSubmissions(await getSubmissions())
  }

  useEffect(() => { refresh() }, [])

  useEffect(() => {
    if (!currentId) return
    const timer = setInterval(async () => {
      try {
        const status = await getStatus(currentId)
        setStepLabel(status.step_label || status.status)
        if (status.status === 'GRADED' || status.status === 'FAILED') {
          clearInterval(timer)
          const full = await getSubmission(currentId)
          setRequirements(full.problem_parsed || null)
          refresh()
        }
      } catch (_) {
        clearInterval(timer)
      }
    }, 2000)
    return () => clearInterval(timer)
  }, [currentId])

  async function handleSubmit() {
    if (!file) return
    setParsing(true)
    try {
      const parsed = await parseProblem(file)
      setRequirements(parsed.problem_parsed)
    } finally {
      setParsing(false)
    }
  }

  async function handleConfirm() {
    const out = await gradeSubmission(file, githubUrl)
    setCurrentId(out.submission_id)
    navigate(`/report/${out.submission_id}`)
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <h1 className="text-3xl font-bold">Take-Home Project Grader</h1>
      <UploadForm
        file={file}
        githubUrl={githubUrl}
        setGithubUrl={setGithubUrl}
        setFile={setFile}
        onSubmit={handleSubmit}
        disabled={!file || !githubUrl || parsing}
      />
      <RequirementsPreview parsed={requirements} onConfirm={handleConfirm} onReset={() => setRequirements(null)} />
      <ProgressTracker stepLabel={stepLabel} />
      <SubmissionsTable submissions={submissions} />
    </div>
  )
}
