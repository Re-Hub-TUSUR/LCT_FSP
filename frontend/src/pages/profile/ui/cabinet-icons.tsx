export type CabinetIcon = 'home' | 'inbox' | 'user' | 'badge' | 'company' | 'sliders'

const PATHS: Record<CabinetIcon, string> = {
  home: 'M3 9.2L10 3.8l7 5.4V16.5H3z M8 16.5v-4.2h4v4.2',
  inbox: 'M3 11l2.2-6h9.6L17 11v5H3z M3 11h4.2l1 2h3.6l1-2H17',
  user: 'M10 3.8a3.2 3.2 0 1 1 0 6.4a3.2 3.2 0 1 1 0-6.4z M3.8 17c.8-3.1 3.3-4.6 6.2-4.6s5.4 1.5 6.2 4.6',
  badge: 'M10 3.4a4.6 4.6 0 1 1 0 9.2a4.6 4.6 0 1 1 0-9.2z M7 12l-1.2 5 4.2-2 4.2 2-1.2-5',
  company: 'M3.5 16.5V5.5l6-2v13 M9.5 7.5h7v9 M2.5 16.5h15 M6 8h1M6 11h1M12.5 10.5h1M12.5 13.5h1',
  sliders:
    'M3.5 6h7.5M15.5 6h1M3.5 14h2M10 14h6.5 M13.2 4a2 2 0 1 1 0 4a2 2 0 1 1 0-4z M7.8 12a2 2 0 1 1 0 4a2 2 0 1 1 0-4z',
}

export function Icon({ name }: { name: CabinetIcon }) {
  return (
    <svg className="cabinet-icon" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path
        d={PATHS[name]}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function LockIcon() {
  return (
    <svg className="cabinet-icon cabinet-icon--small" viewBox="0 0 20 20" aria-hidden="true">
      <rect
        x="4.5"
        y="9"
        width="11"
        height="8"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path d="M7 9V6.6a3 3 0 0 1 6 0V9" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  )
}
