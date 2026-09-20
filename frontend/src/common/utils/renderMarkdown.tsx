import type { ReactNode } from 'react'

/**
 * A minimal, dependency-free renderer for the plain markdown that
 * fireguard-agent-report's LLMs produce (headings, bullet lists, bold text).
 * It intentionally does not support the full CommonMark spec — just enough
 * to make an executive summary readable without pulling in a markdown library.
 */
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const segments = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean)
  return segments.map((segment, index) => {
    if (segment.startsWith('**') && segment.endsWith('**')) {
      return (
        <strong key={`${keyPrefix}-${index}`} className="font-semibold text-slate-900">
          {segment.slice(2, -2)}
        </strong>
      )
    }
    return <span key={`${keyPrefix}-${index}`}>{segment}</span>
  })
}

export function renderMarkdown(markdown: string): ReactNode {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n')
  const blocks: ReactNode[] = []
  let listBuffer: string[] = []

  function flushList() {
    if (listBuffer.length === 0) return
    blocks.push(
      <ul key={`list-${blocks.length}`} className="list-disc space-y-1 pl-5 text-sm text-slate-700">
        {listBuffer.map((item, index) => (
          <li key={index}>{renderInline(item, `li-${blocks.length}-${index}`)}</li>
        ))}
      </ul>,
    )
    listBuffer = []
  }

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim()
    if (line === '') {
      flushList()
      return
    }
    const heading = /^(#{1,3})\s+(.*)$/.exec(line)
    if (heading) {
      flushList()
      const level = heading[1].length
      const text = heading[2]
      const className =
        level === 1
          ? 'text-lg font-semibold text-slate-900'
          : level === 2
            ? 'text-base font-semibold text-slate-900'
            : 'text-sm font-semibold uppercase tracking-wide text-slate-500'
      blocks.push(
        <p key={`h-${index}`} className={className}>
          {renderInline(text, `h-${index}`)}
        </p>,
      )
      return
    }
    const bullet = /^[-*]\s+(.*)$/.exec(line)
    if (bullet) {
      listBuffer.push(bullet[1])
      return
    }
    flushList()
    blocks.push(
      <p key={`p-${index}`} className="text-sm leading-relaxed text-slate-700">
        {renderInline(line, `p-${index}`)}
      </p>,
    )
  })
  flushList()

  return <div className="space-y-3">{blocks}</div>
}
