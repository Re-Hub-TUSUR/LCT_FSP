import type { ReactNode } from 'react'
import { SignupPanel } from '@/features/start-signup'
import { LEGAL, MEDIA } from '../config/content'
import './landing-hero.css'

type Props = {
  /** Site header is a separate widget, so the page passes it in as a slot. */
  header: ReactNode
}

export function LandingHero({ header }: Props) {
  return (
    <main className="hero">
      <div className="hero__media" aria-hidden="true">
        <video
          className="hero__video"
          src={MEDIA.video}
          poster={MEDIA.poster}
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        />
      </div>
      <div className="hero__scrim" aria-hidden="true" />

      {header}

      <div className="hero__body">
        <SignupPanel />
      </div>

      <footer className="legal">
        <p>
          {LEGAL.before}
          <a href={LEGAL.privacy.href}>{LEGAL.privacy.label}</a>
          {LEGAL.between}
          <a href={LEGAL.terms.href}>{LEGAL.terms.label}</a>
          {LEGAL.after}
        </p>
      </footer>
    </main>
  )
}
