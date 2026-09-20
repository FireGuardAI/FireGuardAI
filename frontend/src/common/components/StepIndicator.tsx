import { CheckIcon } from './icons'

export function StepIndicator({ steps, currentIndex }: { steps: string[]; currentIndex: number }) {
  return (
    <ol className="flex items-center gap-3">
      {steps.map((step, index) => {
        const isComplete = index < currentIndex
        const isActive = index === currentIndex
        return (
          <li key={step} className="flex items-center gap-3">
            <span className="flex items-center gap-2">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  isComplete
                    ? 'bg-slate-900 text-white'
                    : isActive
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-400'
                }`}
              >
                {isComplete ? <CheckIcon className="h-3.5 w-3.5" /> : index + 1}
              </span>
              <span className={`text-sm ${isActive ? 'font-medium text-slate-900' : 'text-slate-400'}`}>{step}</span>
            </span>
            {index < steps.length - 1 && <span className="h-px w-8 bg-slate-200" />}
          </li>
        )
      })}
    </ol>
  )
}
