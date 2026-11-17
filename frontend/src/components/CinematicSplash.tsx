import { useCallback, useEffect, useRef, useState } from 'react'
import type { PointerEvent as ReactPointerEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'

const SESSION_KEY = 'shopwise.intro.v1'
const AUTO_DISMISS_MS = 3800
const EXIT_MS = 1100

function shouldShowIntro(pathname: string, search: string) {
  if (pathname !== '/') return false
  if (typeof window === 'undefined') return false
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false

  const forced = new URLSearchParams(search).get('intro') === '1'
  if (forced) return true

  try {
    return window.sessionStorage.getItem(SESSION_KEY) !== 'seen'
  } catch {
    return true
  }
}

export function CinematicSplash() {
  const location = useLocation()
  const [visible, setVisible] = useState(() => shouldShowIntro(location.pathname, location.search))
  const [ready, setReady] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const splashRef = useRef<HTMLDivElement>(null)
  const autoDismissRef = useRef<number | null>(null)
  const exitRef = useRef<number | null>(null)
  const leavingRef = useRef(false)

  const dismiss = useCallback(() => {
    if (leavingRef.current) return
    leavingRef.current = true
    setLeaving(true)
    exitRef.current = window.setTimeout(() => setVisible(false), EXIT_MS)
  }, [])

  useEffect(() => {
    if (!visible) return

    try {
      window.sessionStorage.setItem(SESSION_KEY, 'seen')
    } catch {
      // Session storage can be unavailable in strict privacy modes.
    }

    document.body.classList.add('intro-lock')
    const frame = window.requestAnimationFrame(() => {
      setReady(true)
      splashRef.current?.focus({ preventScroll: true })
    })
    autoDismissRef.current = window.setTimeout(dismiss, AUTO_DISMISS_MS)

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') dismiss()
    }
    window.addEventListener('keydown', onKeyDown)

    return () => {
      window.cancelAnimationFrame(frame)
      if (autoDismissRef.current) window.clearTimeout(autoDismissRef.current)
      if (exitRef.current) window.clearTimeout(exitRef.current)
      window.removeEventListener('keydown', onKeyDown)
      document.body.classList.remove('intro-lock')
    }
  }, [dismiss, visible])

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const node = splashRef.current
    if (!node) return

    const x = event.clientX / window.innerWidth - 0.5
    const y = event.clientY / window.innerHeight - 0.5
    node.style.setProperty('--intro-shift-x', `${(x * 18).toFixed(2)}px`)
    node.style.setProperty('--intro-shift-y', `${(y * 14).toFixed(2)}px`)
    node.style.setProperty('--intro-spot-x', `${(50 + x * 14).toFixed(2)}%`)
    node.style.setProperty('--intro-spot-y', `${(44 + y * 14).toFixed(2)}%`)
  }

  if (!visible) return null

  return (
    <div
      ref={splashRef}
      className={`intro-splash${ready ? ' is-ready' : ''}${leaving ? ' is-leaving' : ''}`}
      role="dialog"
      aria-modal="true"
      aria-label="Shopwise introduction"
      tabIndex={-1}
      onPointerMove={handlePointerMove}
    >
      <div className="intro-splash__grain" aria-hidden="true" />
      <div className="intro-splash__spotlight" aria-hidden="true" />

      <header className="intro-splash__top">
        <span className="intro-splash__wordmark">
          shopwise<span>.</span>
        </span>
        <span className="intro-splash__meta">Considered things for everyday living</span>
        <button type="button" className="intro-splash__skip" onClick={dismiss}>
          Skip intro <ArrowRight size={15} />
        </button>
      </header>

      <div className="intro-splash__stage">
        <section className="intro-splash__copy" aria-label="Shopwise introduction">
          <span className="intro-splash__eyebrow">
            <Sparkles size={13} /> The new home edit · Vol. 04
          </span>

          <h1 className="intro-splash__title">
            <span className="intro-splash__line">
              <span>Objects with</span>
            </span>
            <span className="intro-splash__line">
              <span>a little more</span>
            </span>
            <span className="intro-splash__line intro-splash__line--accent">
              <span>
                soul<span className="intro-splash__title-dot">.</span>
              </span>
            </span>
          </h1>

          <p className="intro-splash__lede">
            A living shop window, arranged around you — one thousand considered pieces, matched by a
            recommender that learns what you love.
          </p>

          <div className="intro-splash__progress-row">
            <span className="intro-splash__progress">
              <span />
            </span>
            <span className="intro-splash__progress-label">Curating your edit</span>
          </div>
        </section>

        <div className="intro-splash__visual" aria-hidden="true">
          <span className="intro-splash__watermark">S</span>
          <span className="intro-splash__halo" />

          <div className="intro-splash__poster">
            <img src="/static/auth-visual.svg" alt="" />
            <span className="intro-splash__poster-label">The autumn / winter edit</span>
          </div>

          <div className="intro-splash__float intro-splash__float--one">
            <div className="intro-splash__float-inner">
              <img src="/static/categories/kitchen-dining.svg" alt="" />
              <span>Kitchen &amp; Dining</span>
            </div>
          </div>

          <div className="intro-splash__float intro-splash__float--two">
            <div className="intro-splash__float-inner">
              <img src="/static/categories/textiles.svg" alt="" />
              <span>Textiles</span>
            </div>
          </div>

          <div className="intro-splash__seal">
            <span>Shopwise</span>
            <small>MMXXVI</small>
          </div>
        </div>
      </div>

      <footer className="intro-splash__bottom">
        <span>01 — 1,000 pieces · 13 curated edits</span>
        <span>Personalised by Shopwise ML</span>
      </footer>
    </div>
  )
}
