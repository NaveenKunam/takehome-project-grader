import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

function scoreColor(score) {
  if (score >= 80) return 'text-green-600'
  if (score >= 50) return 'text-amber-600'
  return 'text-red-600'
}

function recColor(rec) {
  if (rec === 'Strong Yes') return 'bg-green-100 text-green-700'
  if (rec === 'Yes') return 'bg-teal-100 text-teal-700'
  if (rec === 'Maybe') return 'bg-amber-100 text-amber-700'
  if (rec === 'No') return 'bg-red-100 text-red-700'
  return 'bg-slate-100 text-slate-700'
}

export default function SubmissionsTable({ submissions }) {
  const [selected, setSelected] = useState(new Set())
  const navigate = useNavigate()

  function toggle(id) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function handleCompare() {
    navigate(`/compare?ids=${[...selected].join(',')}`)
  }

  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Past Submissions</h3>
        {selected.size >= 2 && (
          <button onClick={handleCompare} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white">
            Compare {selected.size} candidates
          </button>
        )}
      </div>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b">
            <th className="w-8"></th>
            <th>Repo</th><th>Assignment</th><th>Type</th><th>Score</th><th>Recommendation</th><th>Date</th><th>View</th>
          </tr>
        </thead>
        <tbody>
          {submissions.map((s) => (
            <tr key={s.id} className={`border-b ${selected.has(s.id) ? 'bg-blue-50' : ''}`}>
              <td className="py-1">
                <input
                  type="checkbox"
                  checked={selected.has(s.id)}
                  onChange={() => toggle(s.id)}
                  className="h-4 w-4 cursor-pointer accent-blue-600"
                />
              </td>
              <td>{s.repo_owner}/{s.repo_name}</td>
              <td>{s.assignment_title}</td>
              <td>{s.assignment_type}</td>
              <td className={scoreColor(s.total_score || 0)}>{s.total_score ?? '-'}</td>
              <td><span className={`rounded px-2 py-1 text-xs ${recColor(s.hire_recommendation)}`}>{s.hire_recommendation || '-'}</span></td>
              <td>{new Date(s.submitted_at).toLocaleString()}</td>
              <td><Link className="text-blue-600" to={`/report/${s.id}`}>View</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
      {submissions.length >= 2 && selected.size < 2 && (
        <p className="mt-2 text-xs text-slate-400">Select 2 or more candidates to compare</p>
      )}
    </div>
  )
}
