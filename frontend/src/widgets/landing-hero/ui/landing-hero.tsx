import type { ReactNode } from 'react'
import { SignupPanel } from '@/features/start-signup'
import { LEGAL } from '../config/content'
import { FilmRibbon } from './film-ribbon'
import './landing-hero.css'

type Props = {
  /** Site header is a separate widget, so the page passes it in as a slot. */
  header: ReactNode
}

export function LandingHero({ header }: Props) {
  return (
    <main className="hero">
      <div className="hero__glow" aria-hidden="true" />
      <FilmRibbon />

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
