export default function UploadForm({ file, githubUrl, setGithubUrl, setFile, onSubmit, disabled }) {
  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <h2 className="mb-4 text-xl font-semibold">Submission Form</h2>
      <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files?.[0] || null)} className="mb-3 block w-full rounded border p-2" />
      {file && <p className="mb-3 text-sm text-slate-600">Selected: {file.name}</p>}
      <input value={githubUrl} onChange={(e) => setGithubUrl(e.target.value)} placeholder="https://github.com/candidate/repo" className="mb-3 w-full rounded border p-2" />
      <button onClick={onSubmit} disabled={disabled} className="rounded bg-blue-600 px-4 py-2 text-white disabled:bg-slate-300">Grade This Submission</button>
    </div>
  )
}
