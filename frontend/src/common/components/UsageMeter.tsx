export function UsageMeter({ used, limit }: { used: number; limit: number }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0
  const remaining = Math.max(limit - used, 0)
  return (
    <div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold text-slate-900">{used}</span>
        <span className="text-sm text-slate-500">of {limit} reports used</span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-orange-500" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-2 text-xs text-slate-500">
        {remaining} report{remaining === 1 ? '' : 's'} left this month.
      </p>
    </div>
  )
}
