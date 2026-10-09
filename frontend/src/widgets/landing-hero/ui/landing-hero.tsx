import { SignupPanel } from '@/features/start-signup'
import { MEDIA } from '../config/content'
import { FilmGlitch } from './film-glitch'
import { LandingChapters } from './landing-chapters'
import './landing-hero.css'

export function LandingHero() {
  return (
    <main className="landing">
      <div className="landing__film" aria-hidden="true">
        <div className="landing__reel">
          <FilmGlitch poster={MEDIA.poster} />
        </div>
      </div>

      <section className="hero">
        <div className="hero__media" aria-hidden="true" />
        <div className="hero__scrim" aria-hidden="true" />
        <div className="hero__bar" aria-hidden="true" />

        <div className="hero__body">
          <SignupPanel />
        </div>
      </section>

      <LandingChapters />
    </main>
  )
}
