const SECTION_NAMES = [
  'Problem Solving',
  'Tech Stack Choice',
  'Code Quality',
  'Red Flags',
  'Hire Recommendation',
]

function parseSections(summary = '') {
  const sections = {}
  for (let i = 0; i < SECTION_NAMES.length; i += 1) {
    const current = SECTION_NAMES[i]
    const next = SECTION_NAMES[i + 1]
    const pattern = next
      ? new RegExp(`(?:\\d+\\.\\s*)?${current}[\\s\\S]*?(?=(?:\\d+\\.\\s*)?${next})`, 'i')
      : new RegExp(`(?:\\d+\\.\\s*)?${current}[\\s\\S]*$`, 'i')
    const match = summary.match(pattern)
    sections[current] = match ? match[0].replace(new RegExp(`^(?:\\d+\\.\\s*)?${current}\\s*`, 'i'), '').trim() : ''
  }
  return sections
}

export default function AIEvaluation({ summary }) {
  const sections = parseSections(summary || '')
  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="font-semibold">AI Evaluation</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {SECTION_NAMES.map((name) => (
          <div key={name} className={`rounded border p-3 ${name === 'Hire Recommendation' ? 'border-blue-300 bg-blue-50' : ''}`}>
            <h4 className="font-medium">{name}</h4>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{sections[name] || 'Not available'}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
