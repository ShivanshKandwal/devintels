import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Menu, X, Github } from 'lucide-react'
import { useDemoMode } from '../context/DemoModeContext'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/landscape', label: 'Landscape' },
  { to: '/analyzer', label: 'Analyzer' },
  { to: '/forecast', label: 'Forecast' },
  { to: '/tribe', label: 'Tribe' },
]

export default function Navbar() {
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const { demoMode, setDemoMode } = useDemoMode()

  return (
    <nav className="sticky top-0 z-50 glass-strong">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg animated-gradient flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight text-text-primary">
              Dev<span className="text-purple-accent">Intel</span>
            </span>
          </Link>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-1">
            {links.map((l) => {
              const active = pathname === l.to
              return (
                <Link
                  key={l.to}
                  to={l.to}
                  className={`relative px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                    active
                      ? 'text-purple-accent'
                      : 'text-text-secondary hover:text-text-primary hover:bg-black/[0.04] hover:bg-sky-500/8'
                  }`}
                >
                  {l.label}
                  {active && (
                    <motion.div
                      layoutId="nav-underline"
                      className="absolute bottom-0 left-3 right-3 h-0.5 bg-purple-accent rounded-full"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                </Link>
              )
            })}
          </div>

          {/* Right section */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setDemoMode(!demoMode)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer select-none ${
                demoMode
                  ? 'bg-amber-500/10 text-amber-600 border-amber-500/20 hover:bg-amber-500/20'
                  : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20 hover:bg-emerald-500/20'
              }`}
              title={demoMode ? "Switch to Live API Mode" : "Switch to Demo Mode (Mock Results)"}
            >
              <span className={`w-2 h-2 rounded-full ${demoMode ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
              <span className="hidden sm:inline">{demoMode ? 'Demo Mode' : 'Live API'}</span>
            </button>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="hidden md:flex items-center justify-center w-9 h-9 rounded-lg text-text-secondary hover:text-text-primary hover:bg-black/[0.04] hover:bg-sky-500/8 transition-colors"
            >
              <Github className="w-5 h-5" />
            </a>
            <button
              onClick={() => setOpen(!open)}
              className="md:hidden flex items-center justify-center w-9 h-9 rounded-lg text-text-secondary hover:text-text-primary hover:bg-black/[0.04] hover:bg-sky-500/8 transition-colors"
            >
              {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden overflow-hidden border-t border-slate-200/50"
          >
            <div className="px-4 py-3 space-y-1">
              {links.map((l) => {
                const active = pathname === l.to
                return (
                  <Link
                    key={l.to}
                    to={l.to}
                    onClick={() => setOpen(false)}
                    className={`block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      active
                        ? 'text-purple-accent bg-purple-accent/10'
                        : 'text-text-secondary hover:text-text-primary hover:bg-black/[0.04] hover:bg-sky-500/8'
                    }`}
                  >
                    {l.label}
                  </Link>
                )
              })}
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-black/[0.04] hover:bg-sky-500/8 transition-colors"
              >
                <Github className="w-4 h-4" /> GitHub
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
