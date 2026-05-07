export default function RepoFlags({ githubData }) {
  const flags = []
  if (githubData?.is_fork) flags.push('This repo is a fork')
  if (githubData?.multiple_contributors) flags.push('Multiple contributors detected')
  if (!flags.length) return null
  return <div className="rounded-lg bg-amber-50 p-4 text-amber-900 shadow">{flags.map((f) => <p key={f}>⚠ {f}</p>)}</div>
}
