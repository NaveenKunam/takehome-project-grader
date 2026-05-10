import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { getSubmission } from '../components/api'

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

const featureColors = {
  implemented: 'bg-green-100 text-green-700',
  partial: 'bg-amber-100 text-amber-700',
  missing: 'bg-red-100 text-red-700',
  unclear: 'bg-slate-100 text-slate-700',
}

function Bar({ value, max, color }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  return (
    <div className="mt-1 h-2 rounded bg-slate-200">
      <div className={`h-2 rounded ${color}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

function SectionHeader({ label }) {
  return (
    <tr className="bg-slate-100">
      <td colSpan={100} className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </td>
    </tr>
  )
}

function MetricRow({ label, children }) {
  return (
    <tr className="border-b">
      <td className="w-36 shrink-0 py-2 pr-3 align-top text-sm font-medium text-slate-600">{label}</td>
      {children}
    </tr>
  )
}

export default function Compare() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const ids = (params.get('ids') || '').split(',').filter(Boolean)
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (ids.length < 2) { navigate('/'); return }
    Promise.all(ids.map(getSubmission))
      .then(setSubmissions)
      .finally(() => setLoading(false))
  }, [params.get('ids')])

  if (loading) return <div className="p-8 text-slate-500">Loading candidates...</div>

  // Union of all feature names across submissions
  const allFeatures = [...new Set(
    submissions.flatMap((s) => (s.features_assessment?.features_assessment || []).map((f) => f.feature))
  )]

  const best = (key) => {
    const vals = submissions.map((s) => s[key] || 0)
    const max = Math.max(...vals)
    return (val) => val === max && max > 0
  }
  const isBestScore = best('total_score')
  const isBestProblem = best('problem_solving_score')
  const isBestQuality = best('quality_score')

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/')} className="rounded border px-3 py-1.5 text-sm">
          Back
        </button>
        <h1 className="text-2xl font-bold">Candidate Comparison</h1>
        <span className="text-sm text-slate-500">{submissions.length} candidates</span>
      </div>

      <div className="overflow-x-auto rounded-lg bg-white shadow">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="w-36 px-3 py-3 text-left text-xs font-semibold uppercase text-slate-500"></th>
              {submissions.map((s) => (
                <th key={s.id} className="px-3 py-3 text-left">
                  <a
                    href={s.github_url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold text-blue-700 hover:underline"
                  >
                    {s.repo_owner}/{s.repo_name}
                  </a>
                  <p className="text-xs font-normal text-slate-400">
                    {(s.problem_parsed || {}).assignment_title || '—'}
                  </p>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <SectionHeader label="Overall" />

            <MetricRow label="Total Score">
              {submissions.map((s) => {
                const score = s.total_score || 0
                return (
                  <td key={s.id} className="px-3 py-2 align-top">
                    <span className={`text-2xl font-bold ${scoreColor(score)} ${isBestScore(score) ? 'underline decoration-dotted' : ''}`}>
                      {score}/100
                    </span>
                    {isBestScore(score) && <span className="ml-1 text-xs text-green-600">best</span>}
                  </td>
                )
              })}
            </MetricRow>

            <MetricRow label="Recommendation">
              {submissions.map((s) => (
                <td key={s.id} className="px-3 py-2 align-top">
                  <span className={`rounded px-2 py-1 text-xs ${recColor(s.hire_recommendation)}`}>
                    {s.hire_recommendation || 'Pending'}
                  </span>
                </td>
              ))}
            </MetricRow>

            <SectionHeader label="Scores" />

            <MetricRow label="Problem Solving">
              {submissions.map((s) => {
                const score = s.problem_solving_score || 0
                return (
                  <td key={s.id} className="px-3 py-2 align-top">
                    <p className={`font-semibold ${isBestProblem(score) ? 'text-green-700' : 'text-slate-800'}`}>
                      {score}/50
                    </p>
                    <Bar value={score} max={50} color="bg-blue-500" />
                  </td>
                )
              })}
            </MetricRow>

            <MetricRow label="Code Quality">
              {submissions.map((s) => {
                const score = s.quality_score || 0
                return (
                  <td key={s.id} className="px-3 py-2 align-top">
                    <p className={`font-semibold ${isBestQuality(score) ? 'text-green-700' : 'text-slate-800'}`}>
                      {score}/50
                    </p>
                    <Bar value={score} max={50} color="bg-emerald-500" />
                  </td>
                )
              })}
            </MetricRow>

            <SectionHeader label="Build & Tests" />

            <MetricRow label="Build">
              {submissions.map((s) => {
                const ok = s.grading_data?.build_success
                return (
                  <td key={s.id} className="px-3 py-2 align-top">
                    <span className={ok ? 'text-green-600' : 'text-red-600'}>{ok ? '✓ Pass' : '✗ Fail'}</span>
                  </td>
                )
              })}
            </MetricRow>

            <MetricRow label="Tests">
              {submissions.map((s) => {
                const g = s.grading_data || {}
                const total = g.tests_total || 0
                const passed = g.tests_passed || 0
                const failed = g.tests_failed || 0
                return (
                  <td key={s.id} className="px-3 py-2 align-top">
                    {total === 0 ? (
                      <span className="text-slate-400">No tests</span>
                    ) : (
                      <span>
                        <span className="text-green-600">{passed} pass</span>
                        {failed > 0 && <span className="ml-1 text-red-600">{failed} fail</span>}
                        <span className="ml-1 text-slate-400 text-xs">/ {total}</span>
                      </span>
                    )}
                  </td>
                )
              })}
            </MetricRow>

            <MetricRow label="Lint Errors">
              {submissions.map((s) => {
                const errs = s.grading_data?.lint_errors ?? '—'
                const ok = typeof errs === 'number' && errs < 10
                return (
                  <td key={s.id} className="px-3 py-2 align-top">
                    <span className={ok ? 'text-green-600' : 'text-amber-600'}>{errs}</span>
                  </td>
                )
              })}
            </MetricRow>

            <SectionHeader label="Tech Stack" />

            <MetricRow label="Summary">
              {submissions.map((s) => (
                <td key={s.id} className="px-3 py-2 align-top text-xs text-slate-600">
                  {s.grading_data?.tech_stack_summary || '—'}
                </td>
              ))}
            </MetricRow>

            <MetricRow label="Languages">
              {submissions.map((s) => {
                const langs = Object.keys((s.github_data || {}).language_percentages || {})
                return (
                  <td key={s.id} className="px-3 py-2 align-top">
                    {langs.length > 0
                      ? langs.map((l) => (
                          <span key={l} className="mr-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs">{l}</span>
                        ))
                      : <span className="text-slate-400">—</span>}
                  </td>
                )
              })}
            </MetricRow>

            {allFeatures.length > 0 && (
              <>
                <SectionHeader label="Features" />
                {allFeatures.map((feature) => (
                  <MetricRow key={feature} label={feature}>
                    {submissions.map((s) => {
                      const items = s.features_assessment?.features_assessment || []
                      const found = items.find((f) => f.feature === feature)
                      return (
                        <td key={s.id} className="px-3 py-2 align-top">
                          {found ? (
                            <span className={`rounded px-2 py-0.5 text-xs ${featureColors[found.status] || featureColors.unclear}`}>
                              {found.status}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-300">—</span>
                          )}
                        </td>
                      )
                    })}
                  </MetricRow>
                ))}
              </>
            )}

            <SectionHeader label="GitHub" />

            <MetricRow label="Contributors">
              {submissions.map((s) => (
                <td key={s.id} className="px-3 py-2 align-top">
                  {s.github_data?.contributor_count ?? '—'}
                </td>
              ))}
            </MetricRow>

            <MetricRow label="Created">
              {submissions.map((s) => (
                <td key={s.id} className="px-3 py-2 align-top text-slate-600">
                  {s.github_data?.created_at ? new Date(s.github_data.created_at).toLocaleDateString() : '—'}
                </td>
              ))}
            </MetricRow>

            <MetricRow label="Last push">
              {submissions.map((s) => (
                <td key={s.id} className="px-3 py-2 align-top text-slate-600">
                  {s.github_data?.last_push_at ? new Date(s.github_data.last_push_at).toLocaleDateString() : '—'}
                </td>
              ))}
            </MetricRow>
          </tbody>
        </table>
      </div>
    </div>
  )
}
