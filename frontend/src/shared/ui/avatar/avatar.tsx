import './avatar.css'

/** First letters of the first two words: «Алексей Смирнов» → «АС». */
export function initialsOf(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

type Props = {
  name: string
  /** Photo or logo; initials are shown without it. */
  src?: string | null
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /** `dark` sits on a filled card, `blue` on the page ground. */
  tone?: 'blue' | 'dark'
  className?: string
}

/** Square avatar: a photo, or initials in the accent face. */
export function Avatar({ name, src, size = 'md', tone = 'blue', className }: Props) {
  const classes = ['avatar', `avatar--${size}`, `avatar--${tone}`, className]
    .filter(Boolean)
    .join(' ')
  return (
    <span className={classes} aria-hidden="true">
      {src ? <img src={src} alt="" /> : initialsOf(name)}
    </span>
  )
}
