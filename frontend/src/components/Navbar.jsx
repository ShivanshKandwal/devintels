import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Menu, X, Github } from 'lucide-react'
import { useDemoMode } from '../context/DemoModeContext'

const links = [
  { to: '/', label: 'Overview' },
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
    <header className="flex justify-between items-center px-6 py-3.5 bg-white/40 border border-white/60 backdrop-blur-md shadow-sm rounded-3xl mb-8 relative z-50">
      {/* Brand */}
      <Link to="/" className="flex items-center gap-2.5 group select-none">
        <div className="w-9 h-9 rounded-xl animated-gradient flex items-center justify-center shadow-md shadow-purple-accent/10">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold tracking-tight text-text-primary">
          Dev<span className="text-purple-accent">Intel</span>
        </span>
      </Link>

      {/* Desktop links */}
      <div className="hidden md:flex items-center gap-1.5 select-none">
        {links.map((l) => {
          const active = pathname === l.to
          return (
            <Link
              key={l.to}
              to={l.to}
              className={`relative px-4 py-2.5 rounded-xl text-sm font-bold transition-all duration-250 ${
                active
                  ? 'text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-black/[0.03]'
              }`}
            >
              {active && (
                <motion.div
                  layoutId="nav-active-pill"
                  className="absolute inset-0 bg-gradient-to-tr from-purple-accent to-purple-light rounded-xl shadow shadow-purple-accent/15 z-[-1]"
                  transition={{ type: 'spring', stiffness: 350, damping: 28 }}
                />
              )}
              {l.label}
            </Link>
          )
        })}
      </div>

      {/* Right section */}
      <div className="flex items-center gap-2.5">
        <button
          onClick={() => setDemoMode(!demoMode)}
          className={`flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-bold border transition-all cursor-pointer select-none ${
            demoMode
              ? 'bg-amber-500/10 text-amber-600 border-amber-500/20 hover:bg-amber-500/20 shadow-sm shadow-amber-500/5'
              : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20 hover:bg-emerald-500/20 shadow-sm shadow-emerald-500/5'
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
          className="hidden md:flex items-center justify-center w-10 h-10 rounded-xl bg-white/60 border border-slate-200/60 hover:border-slate-350 text-text-secondary hover:text-text-primary hover:bg-white/90 transition-all shadow-sm"
        >
          <Github className="w-5 h-5" />
        </a>
        <button
          onClick={() => setOpen(!open)}
          className="md:hidden flex items-center justify-center w-10 h-10 rounded-xl bg-white/60 border border-slate-200/60 hover:border-slate-350 text-text-secondary hover:text-text-primary hover:bg-white/90 transition-all shadow-sm"
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="absolute top-full left-0 right-0 mt-2 bg-white/90 backdrop-blur-md border border-white/60 shadow-lg rounded-2xl md:hidden overflow-hidden z-50"
          >
            <div className="px-4 py-3 space-y-1">
              {links.map((l) => {
                const active = pathname === l.to
                return (
                  <Link
                    key={l.to}
                    to={l.to}
                    onClick={() => setOpen(false)}
                    className={`block px-3 py-2.5 rounded-xl text-sm font-bold transition-all ${
                      active
                        ? 'text-purple-accent bg-purple-accent/10'
                        : 'text-text-secondary hover:text-text-primary hover:bg-black/[0.03]'
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
                className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-bold text-text-secondary hover:text-text-primary hover:bg-black/[0.03]"
              >
                <Github className="w-4 h-4" /> GitHub
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
