export default function ScoreBreakdown({ problemSolvingScore, qualityScore, gradingData }) {
  const pScore = problemSolvingScore || 0
  const qScore = qualityScore || 0
  const pPct = Math.min(100, Math.max(0, (pScore / 50) * 100))
  const qPct = Math.min(100, Math.max(0, (qScore / 50) * 100))
  const breakdown = gradingData?.score_breakdown || null

  function Row({ item }) {
    return (
      <div className="flex items-start justify-between gap-3 rounded border p-2 text-sm">
        <div className="min-w-0">
          <p className="font-medium">{item.label}</p>
          {item.evidence && <p className="mt-0.5 break-words text-xs text-slate-600">{item.evidence}</p>}
        </div>
        <div className="shrink-0 font-semibold tabular-nums text-slate-800">{item.awarded}/{item.possible}</div>
      </div>
    )
  }

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="font-semibold">Score Breakdown</h3>
      <div className="mt-2">
        <p className="text-sm">Problem Solving: {pScore}/50</p>
        <div className="mt-1 h-2 rounded bg-slate-200"><div className="h-2 rounded bg-blue-600" style={{ width: `${pPct}%` }} /></div>
      </div>
      <div className="mt-3">
        <p className="text-sm">Code Quality: {qScore}/50</p>
        <div className="mt-1 h-2 rounded bg-slate-200"><div className="h-2 rounded bg-emerald-600" style={{ width: `${qPct}%` }} /></div>
      </div>
      <p className="mt-2 text-xs text-slate-600">Build {gradingData?.build_success ? '✓' : '✗'} | Tests Exist {gradingData?.has_tests ? '✓' : '✗'} | Tests Pass {(gradingData?.tests_total || 0) > 0 && (gradingData?.tests_failed || 0) === 0 ? '✓' : '✗'} | Lint {(gradingData?.lint_errors || 999) < 10 || (gradingData?.pylint_score || 0) >= 6 ? '✓' : '✗'}</p>

      {breakdown && (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <h4 className="text-sm font-semibold">Problem Solving rubric</h4>
            <div className="mt-2 space-y-2">
              {(breakdown.problem_solving || []).map((item, idx) => <Row key={`${item.label}-${idx}`} item={item} />)}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold">Code Quality rubric</h4>
            <div className="mt-2 space-y-2">
              {(breakdown.quality || []).map((item, idx) => <Row key={`${item.label}-${idx}`} item={item} />)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
