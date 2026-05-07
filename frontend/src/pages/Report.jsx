import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ProgressTracker from '../components/ProgressTracker'
import ReportCard from '../components/ReportCard'
import { deleteSubmission, getStatus, getSubmission } from '../components/api'

export default function Report() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [submission, setSubmission] = useState(null)
  const [stepLabel, setStepLabel] = useState('')

  useEffect(() => {
    let timer = null
    async function load() {
      try {
        const full = await getSubmission(id)
        setSubmission(full)
        setStepLabel(full.current_step_label || '')

        if (full.status !== 'GRADED' && full.status !== 'FAILED') {
          timer = setInterval(async () => {
            try {
              const status = await getStatus(id)
              setStepLabel(status.step_label || status.status)
              if (status.status === 'GRADED' || status.status === 'FAILED') {
                clearInterval(timer)
                const updated = await getSubmission(id)
                setSubmission(updated)
                setStepLabel(updated.current_step_label || status.step_label || status.status)
              }
            } catch (_) {
              clearInterval(timer)
            }
          }, 2000)
        }
      } catch (_) {
        navigate('/')
      }
    }

    load()
    return () => {
      if (timer) clearInterval(timer)
    }
  }, [id, navigate])

  async function handleDelete() {
    await deleteSubmission(id)
    navigate('/')
  }

  if (!submission) return <div className="p-6">Loading...</div>

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      {submission.status !== 'GRADED' && <ProgressTracker stepLabel={stepLabel} />}
      <ReportCard submission={submission} onDelete={handleDelete} onBack={() => navigate('/')} />
    </div>
  )
}
