import { useState } from 'react'
import type { ReactNode } from 'react'
import { Sidebar } from '../components/Sidebar'
import { FlameIcon } from '../components/icons'

export function AppLayout({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <div className="print-hidden hidden lg:block">
        <div className="sticky top-0 h-screen">
          <Sidebar />
        </div>
      </div>

      <div className="print-hidden flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 lg:hidden">
        <span className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-orange-500 text-white">
            <FlameIcon className="h-4 w-4" />
          </span>
          <span className="text-sm font-semibold text-slate-900">
            FireGuard<span className="text-orange-500">AI</span>
          </span>
        </span>
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="rounded-md border border-slate-200 px-2.5 py-1.5 text-sm text-slate-600"
        >
          Menu
        </button>
      </div>

      {drawerOpen && (
        <div className="print-hidden fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-slate-900/50"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="relative h-full w-64">
            <Sidebar onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <main className="flex-1 px-4 py-6 sm:px-8 sm:py-8">
        <div className="mx-auto max-w-6xl">{children}</div>
      </main>
    </div>
  )
}
