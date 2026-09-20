import type { SVGProps } from 'react'

export type IconProps = SVGProps<SVGSVGElement>

function base(props: IconProps) {
  return {
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.75,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    ...props,
  }
}

export function FlameIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 2c1.2 2.4 4.5 4.9 4.5 9a4.5 4.5 0 0 1-9 0c0-1.3.5-2.2 1-3-.2 1.4.3 2 1 2.3-.5-2.2 1-3.5 1-5.3.6.8 1.5 1.4 1.5 2.6a2 2 0 0 0 4 0c0-2.6-1.5-4-3-5.6Z" />
    </svg>
  )
}

export function GridIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  )
}

export function PlusIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  )
}

export function SparklesIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2 2M16 16l2 2M18 6l-2 2M8 16l-2 2" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

export function CreditCardIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="2.5" y="5" width="19" height="14" rx="2" />
      <path d="M2.5 10h19" />
    </svg>
  )
}

export function LockIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="4.5" y="10.5" width="15" height="10" rx="2" />
      <path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" />
    </svg>
  )
}

export function SearchIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  )
}

export function ShieldCheckIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3 4.5 6v6c0 4.5 3.2 7.7 7.5 9 4.3-1.3 7.5-4.5 7.5-9V6L12 3Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

export function GraduationCapIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M2 9.5 12 5l10 4.5-10 4.5-10-4.5Z" />
      <path d="M6 12v4.5c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5V12" />
    </svg>
  )
}

export function UploadCloudIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M7 17a4.5 4.5 0 0 1-1-8.9A5.5 5.5 0 0 1 16.9 7a4.5 4.5 0 0 1 .1 9H7Z" />
      <path d="M12 12v6M9.5 14.5 12 12l2.5 2.5" />
    </svg>
  )
}

export function FileTextIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v4h4M9 12h6M9 15.5h6M9 8.5h2" />
    </svg>
  )
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="m9 6 6 6-6 6" />
    </svg>
  )
}

export function ArrowLeftIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M19 12H5M11 6l-6 6 6 6" />
    </svg>
  )
}

export function LogOutIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3" />
      <path d="M16 17l5-5-5-5M21 12H9" />
    </svg>
  )
}

export function CheckIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="m5 12 5 5 9-9" />
    </svg>
  )
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12.5 2.5 2.5 4.5-5" />
    </svg>
  )
}

export function AlertTriangleIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3.5 22 20H2L12 3.5Z" />
      <path d="M12 10v4M12 17.5v.01" />
    </svg>
  )
}

export function XCircleIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="9" />
      <path d="m9.5 9.5 5 5m0-5-5 5" />
    </svg>
  )
}

export function DownloadIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3v12M8 11l4 4 4-4" />
      <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </svg>
  )
}

export function MailIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m4 7 8 6 8-6" />
    </svg>
  )
}

export function BuildingIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="4" y="3" width="10" height="18" rx="1" />
      <path d="M14 8h6v13h-6M7 7h.01M10.5 7h.01M7 10.5h.01M10.5 10.5h.01M7 14h.01M10.5 14h.01" />
    </svg>
  )
}
