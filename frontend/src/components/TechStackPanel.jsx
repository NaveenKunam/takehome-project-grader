export default function TechStackPanel({ githubData, techStackSummary }) {
  const langs = githubData?.language_percentages || {}
  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="font-semibold">Candidate Tech Stack</h3>
      <div className="mt-2 space-y-2">
        {Object.entries(langs).map(([name, pct]) => (
          <div key={name}><div className="flex justify-between text-sm"><span>{name}</span><span>{pct}%</span></div><div className="h-2 rounded bg-slate-200"><div className="h-2 rounded bg-blue-600" style={{ width: `${pct}%` }} /></div></div>
        ))}
      </div>
      <p className="mt-3 text-sm text-slate-600">{techStackSummary}</p>
    </div>
  )
}
