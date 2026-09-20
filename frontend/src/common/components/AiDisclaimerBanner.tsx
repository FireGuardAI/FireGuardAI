import { ShieldCheckIcon } from './icons'

/**
 * Responsible-AI notice shown wherever generated findings are presented.
 * FireGuardAI's reports come from LLMs (Groq/Gemini) reasoning over retrieved
 * regulation text — they are a drafting aid, not a certified inspection.
 */
export function AiDisclaimerBanner({ className = '' }: { className?: string }) {
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 ${className}`}
    >
      <ShieldCheckIcon className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
      <p>
        <span className="font-semibold">AI-generated analysis.</span> This report is produced by an automated
        pipeline for guidance only. It does not replace a licensed fire-safety inspection or sign-off from your
        local Authority Having Jurisdiction (AHJ) — verify every finding before acting on it.
      </p>
    </div>
  )
}
