import AIEvaluation from './AIEvaluation'
import FeaturesPanel from './FeaturesPanel'
import LogViewer from './LogViewer'
import RepoFlags from './RepoFlags'
import ScoreBreakdown from './ScoreBreakdown'
import TechStackPanel from './TechStackPanel'

function scoreColor(score) {
  if (score >= 80) return 'text-green-600'
  if (score >= 50) return 'text-amber-600'
  return 'text-red-600'
}

function recommendationColor(rec) {
  if (rec === 'Strong Yes') return 'bg-green-100 text-green-700'
  if (rec === 'Yes') return 'bg-teal-100 text-teal-700'
  if (rec === 'Maybe') return 'bg-amber-100 text-amber-700'
  if (rec === 'No') return 'bg-red-100 text-red-700'
  return 'bg-slate-100 text-slate-700'
}

export default function ReportCard({ submission, onDelete, onBack }) {
  const parsed = submission.problem_parsed || {}
  const features = submission.features_assessment || {}
  const grading = submission.grading_data || {}
  const github = submission.github_data || {}
  const repoUrl = submission.github_url
  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-white p-6 shadow">
        <a href={repoUrl} target="_blank" rel="noreferrer" className="text-2xl font-bold text-blue-700 hover:underline">
          {submission.repo_owner}/{submission.repo_name}
        </a>
        <p className="text-slate-500">{parsed.assignment_title} ({parsed.assignment_type})</p>
        <p className={`text-4xl font-bold ${scoreColor(submission.total_score || 0)}`}>{submission.total_score || 0}/100</p>
        <p className={`mt-1 inline-block rounded px-3 py-1 text-sm ${recommendationColor(submission.hire_recommendation)}`}>
          {submission.hire_recommendation || 'Pending'}
        </p>
        <div className="mt-4 grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
          <p><span className="text-slate-500">Contributors:</span> {github.contributor_count ?? '-'}</p>
          <p><span className="text-slate-500">Created:</span> {github.created_at ? new Date(github.created_at).toLocaleDateString() : '-'}</p>
          <p><span className="text-slate-500">Last push:</span> {github.last_push_at ? new Date(github.last_push_at).toLocaleDateString() : '-'}</p>
          <p><span className="text-slate-500">Languages:</span> {Object.keys(github.language_percentages || {}).length}</p>
        </div>
        <div className="mt-4 flex gap-2"><button onClick={onBack} className="rounded border px-3 py-2">Grade Another</button><button onClick={onDelete} className="rounded bg-red-600 px-3 py-2 text-white">Delete</button></div>
      </div>
      <TechStackPanel githubData={submission.github_data} techStackSummary={grading.tech_stack_summary} />
      <FeaturesPanel assessment={features} />
      <RepoFlags githubData={submission.github_data} />
      <ScoreBreakdown problemSolvingScore={submission.problem_solving_score} qualityScore={submission.quality_score} gradingData={grading} />
      <AIEvaluation summary={submission.ai_summary} />
      <LogViewer commands={grading.commands} />
    </div>
  )
}
