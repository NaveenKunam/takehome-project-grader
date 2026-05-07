const STEPS = ['Reading problem statement','Extracting requirements','Fetching GitHub data','Cloning repository','Running build and tests','Scanning source code','Calculating score','Generating evaluation','Done']

export default function ProgressTracker({ stepLabel }) {
  if (!stepLabel) return null
  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <h3 className="mb-3 text-lg font-semibold">Progress</h3>
      <ul className="space-y-1 text-sm">
        {STEPS.map((step) => (
          <li key={step} className={stepLabel.includes(step) ? 'animate-pulse font-semibold text-blue-600' : 'text-slate-500'}>{step}</li>
        ))}
      </ul>
    </div>
  )
}
