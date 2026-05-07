export default function RequirementsPreview({ parsed, onConfirm, onReset }) {
  if (!parsed) return null
  const hasRequirements = (parsed.required_features || []).length > 0
  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <h3 className="text-lg font-semibold">Problem Document Preview</h3>
      <p className="mt-2 font-medium">{parsed.assignment_title || 'Unknown Assignment'}</p>
      <p className="text-sm text-slate-500">Type: {parsed.assignment_type || 'unknown'}</p>
      {!hasRequirements ? (
        <p className="mt-3 text-sm text-slate-700">
          No explicit requirements were extracted from this document. Grading will use a tech-stack agnostic rubric based on repo signals (build/tests/lint/routes/deps).
        </p>
      ) : (
        <ul className="mt-3 list-disc pl-6 text-sm">
          {(parsed.required_features || []).map((f) => <li key={f}>{f}</li>)}
        </ul>
      )}
      <div className="mt-4 flex gap-2">
        <button onClick={onConfirm} className="rounded bg-emerald-600 px-4 py-2 text-white">Looks correct, start grading</button>
        <button onClick={onReset} className="rounded border px-4 py-2">Re-upload</button>
      </div>
    </div>
  )
}
