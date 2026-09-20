import { useEffect, useRef, useState } from 'react'
import type { DragEvent, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../../common/hooks/useAuth'
import { ApiError } from '../../../common/services/api'
import { saveAnalysisRecord, submitPdfAnalysis, submitTextAnalysis } from '../../../common/services/analysisService'
import { PLAN_CATALOG } from '../../../common/types/account'
import { FileTextIcon, LockIcon, UploadCloudIcon } from '../../../common/components/icons'

const STEPS = ['Sanitizing input', 'Retrieving regulations', 'Running compliance audit', 'Drafting report']

const EXAMPLE_DESCRIPTION =
  'A 5-storey mixed-use office building in Colombo with underground parking, two stairwells, ' +
  'a wet-riser fire suppression system, smoke detectors on every floor and a single main entrance ' +
  'used as the primary evacuation route.'

const MAX_PDF_BYTES = 15 * 1024 * 1024

type Mode = 'text' | 'pdf'
type Phase = 'idle' | 'running' | 'error'

function NewAnalysisPage() {
  const { account, token, refreshAccount } = useAuth()
  const navigate = useNavigate()

  const canUsePdf = account?.pdf_export_enabled ?? false
  const [mode, setMode] = useState<Mode>('text')
  const [description, setDescription] = useState('')
  const [buildingName, setBuildingName] = useState('')
  const [auditorNotes, setAuditorNotes] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)

  const [phase, setPhase] = useState<Phase>('idle')
  const [stepIndex, setStepIndex] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  if (!account || !token) return null
  const plan = PLAN_CATALOG[account.plan]

  const isOutOfReports =
    (account.plan === 'student' || account.plan === 'basic') && (account.reports_remaining ?? 0) <= 0

  function quotaHint(): string {
    if (!account) return ''
    if (account.plan === 'student') {
      return `This run uses 1 of your remaining ${account.reports_remaining ?? 0} monthly student reports.`
    }
    if (account.plan === 'basic') {
      return `This run uses 1 report credit. You have ${account.reports_remaining ?? 0} left.`
    }
    return `Unlimited reports on your ${plan.name} plan.`
  }

  function handleFileChange(next: File | null) {
    setFileError(null)
    if (next && next.size > MAX_PDF_BYTES) {
      setFileError('That file is larger than the 15 MB limit.')
      setFile(null)
      return
    }
    if (next && next.type !== 'application/pdf') {
      setFileError('Only PDF files are supported.')
      setFile(null)
      return
    }
    setFile(next)
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    handleFileChange(event.dataTransfer.files[0] ?? null)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!account || !token) return
    if (mode === 'pdf' && !file) {
      setFileError('Select a PDF to upload.')
      return
    }

    setPhase('running')
    setStepIndex(0)
    setErrorMessage(null)
    intervalRef.current = setInterval(() => {
      setStepIndex((current) => Math.min(current + 1, STEPS.length - 2))
    }, 1400)

    try {
      const report =
        mode === 'pdf' && file
          ? await submitPdfAnalysis(token, file, buildingName || undefined, auditorNotes || undefined)
          : await submitTextAnalysis(token, {
              rawPrompt: description,
              buildingName: buildingName || undefined,
              auditorNotes: auditorNotes || undefined,
            })

      if (intervalRef.current) clearInterval(intervalRef.current)
      setStepIndex(STEPS.length - 1)
      saveAnalysisRecord(account.id, report)
      await refreshAccount()
      navigate(`/analysis/${report.id}`)
    } catch (err) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      setPhase('error')
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong while running the audit. Please try again.',
      )
    }
  }

  if (phase === 'running' || phase === 'error') {
    return (
      <div className="mx-auto max-w-xl">
        <h1 className="text-2xl font-semibold text-slate-900">Running your audit</h1>
        <p className="mt-1 text-sm text-slate-500">This can take up to a few minutes on larger buildings.</p>

        <div className="mt-8 space-y-4 rounded-xl border border-slate-200 bg-white p-6">
          {STEPS.map((step, index) => {
            const done = phase === 'running' ? index < stepIndex : index <= stepIndex
            const active = phase === 'running' && index === stepIndex
            return (
              <div key={step} className="flex items-center gap-3">
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                    done ? 'bg-emerald-500 text-white' : active ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  {done ? '✓' : index + 1}
                </span>
                <span className={`text-sm ${active || done ? 'text-slate-900' : 'text-slate-400'}`}>{step}</span>
              </div>
            )
          })}
        </div>

        {phase === 'error' && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">{errorMessage}</p>
            <div className="mt-3 flex gap-3">
              <button
                type="button"
                onClick={() => setPhase('idle')}
                className="rounded-md bg-white px-3 py-1.5 text-sm font-medium text-red-700 ring-1 ring-inset ring-red-300 hover:bg-red-100"
              >
                Try again
              </button>
              <Link to="/dashboard" className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100">
                Back to dashboard
              </Link>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">New analysis</p>
      <h1 className="mt-1 text-2xl font-semibold text-slate-900">Audit a building against fire code</h1>
      <p className="mt-1 text-sm text-slate-500">
        The pipeline retrieves the code sections that apply to your occupancy class, then audits every clause and
        cites its source.
      </p>

      <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
        <div>
          <p className="mb-2 text-sm font-medium text-slate-700">Input method</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => setMode('text')}
              className={`rounded-xl border p-4 text-left ${
                mode === 'text' ? 'border-orange-500 ring-1 ring-orange-500' : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <FileTextIcon className="h-5 w-5 text-orange-500" />
              <p className="mt-2 text-sm font-semibold text-slate-900">Describe your building</p>
              <p className="mt-1 text-xs text-slate-500">Free text — occupancy, size, egress, suppression. Available on every plan.</p>
            </button>

            <button
              type="button"
              disabled={!canUsePdf}
              onClick={() => canUsePdf && setMode('pdf')}
              className={`relative rounded-xl border p-4 text-left ${
                !canUsePdf
                  ? 'cursor-not-allowed border-dashed border-slate-200 opacity-70'
                  : mode === 'pdf'
                    ? 'border-orange-500 ring-1 ring-orange-500'
                    : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              {!canUsePdf && (
                <span className="absolute right-4 top-4 inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                  <LockIcon className="h-3 w-3" /> Locked
                </span>
              )}
              <UploadCloudIcon className="h-5 w-5 text-orange-500" />
              <p className="mt-2 text-sm font-semibold text-slate-900">Upload building plan (PDF)</p>
              {canUsePdf ? (
                <p className="mt-1 text-xs text-slate-500">Upload architectural drawings for a deeper analysis.</p>
              ) : (
                <>
                  <p className="mt-1 text-xs text-slate-500">
                    {plan.name} accounts are text-only. Upgrade to Basic or above to analyze drawings.
                  </p>
                  <Link to="/pricing" className="mt-1 inline-block text-xs font-medium text-orange-600 hover:text-orange-700">
                    Upgrade to unlock &rarr;
                  </Link>
                </>
              )}
            </button>
          </div>
        </div>

        {mode === 'text' ? (
          <div>
            <div className="flex items-center justify-between">
              <label htmlFor="description" className="text-sm font-medium text-slate-700">
                Building description
              </label>
              <button
                type="button"
                onClick={() => setDescription(EXAMPLE_DESCRIPTION)}
                className="text-xs font-medium text-orange-600 hover:text-orange-700"
              >
                Use example
              </button>
            </div>
            <textarea
              id="description"
              required
              maxLength={60000}
              rows={6}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Occupancy class, floor area, number of storeys, exits, sprinkler/alarm systems, storage type…"
              className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />
            <p className="mt-1 text-xs text-slate-400">{description.length} characters. More detail produces more precise citations.</p>
          </div>
        ) : (
          <div>
            <p className="mb-2 text-sm font-medium text-slate-700">Building plan</p>
            <div
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
              className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-slate-300 px-6 py-10 text-center"
            >
              <UploadCloudIcon className="h-8 w-8 text-slate-400" />
              {file ? (
                <div>
                  <p className="text-sm font-medium text-slate-900">{file.name}</p>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="mt-1 text-xs font-medium text-red-600 hover:text-red-700"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <>
                  <p className="text-sm text-slate-600">Drag and drop a PDF here, or</p>
                  <label className="cursor-pointer text-sm font-medium text-orange-600 hover:text-orange-700">
                    browse files
                    <input
                      type="file"
                      accept="application/pdf"
                      className="hidden"
                      onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
                    />
                  </label>
                  <p className="text-xs text-slate-400">Up to 15 MB.</p>
                </>
              )}
            </div>
            {fileError && <p className="mt-2 text-sm text-red-600">{fileError}</p>}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="buildingName" className="mb-1 block text-sm font-medium text-slate-700">
              Building name <span className="text-slate-400">(optional)</span>
            </label>
            <input
              id="buildingName"
              value={buildingName}
              maxLength={200}
              onChange={(event) => setBuildingName(event.target.value)}
              placeholder="Meridian Logistics Hub"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />
          </div>
          <div>
            <label htmlFor="auditorNotes" className="mb-1 block text-sm font-medium text-slate-700">
              Auditor notes <span className="text-slate-400">(optional)</span>
            </label>
            <input
              id="auditorNotes"
              value={auditorNotes}
              maxLength={4000}
              onChange={(event) => setAuditorNotes(event.target.value)}
              placeholder="Focus on high-piled storage in the east bay"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />
          </div>
        </div>

        <div className="flex flex-col items-start gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-slate-500">
            {isOutOfReports ? (
              <span className="text-red-600">
                You've used all your reports this month.{' '}
                <Link to="/pricing" className="font-medium underline">
                  Upgrade to continue
                </Link>
                .
              </span>
            ) : (
              quotaHint()
            )}
          </p>
          <button
            type="submit"
            disabled={isOutOfReports || (mode === 'text' && description.trim().length === 0)}
            className="w-full shrink-0 rounded-lg bg-orange-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
          >
            Run compliance audit
          </button>
        </div>
      </form>
    </div>
  )
}

export default NewAnalysisPage
