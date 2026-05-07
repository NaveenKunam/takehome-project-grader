export default function LogViewer({ commands }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="font-semibold">Raw Logs</h3>
      <details className="mt-2"><summary>Show command outputs</summary><div className="space-y-2 mt-2">{(commands || []).map((c, idx) => <div key={idx} className="rounded border p-2"><p className="font-medium">{c.name}</p><pre className="max-h-48 overflow-auto text-xs">{c.output}</pre></div>)}</div></details>
    </div>
  )
}
