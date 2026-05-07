const colors = { implemented: 'bg-green-100 text-green-700', partial: 'bg-amber-100 text-amber-700', missing: 'bg-red-100 text-red-700', unclear: 'bg-slate-100 text-slate-700' }

export default function FeaturesPanel({ assessment }) {
  const items = assessment?.features_assessment || []
  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="font-semibold">Feature Assessment</h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-slate-700">
          No explicit feature checklist was available. The score uses a rubric based on repo signals; see “Score Breakdown” for point-by-point grading.
        </p>
      ) : (
        <div className="mt-2 space-y-2">
          {items.map((i, idx) => (
            <div key={`${i.feature}-${idx}`} className="rounded border p-2">
              <div className="flex items-center justify-between">
                <p className="font-medium">{i.feature}</p>
                <span className={`rounded px-2 py-1 text-xs ${colors[i.status]}`}>{i.status}</span>
              </div>
              <p className="text-sm text-slate-600">{i.evidence}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
