import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Users, Layers, Cpu, BarChart3, Map, Brain, TrendingUp, Search,
  ArrowRight, Sparkles, Github, ExternalLink
} from 'lucide-react'
import StatCard from '../components/StatCard'

/* ── Animated background particles ───────────────────────────────── */
function Particles() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId
    let particles = []

    const resize = () => {
      canvas.width = canvas.offsetWidth * devicePixelRatio
      canvas.height = canvas.offsetHeight * devicePixelRatio
      ctx.scale(devicePixelRatio, devicePixelRatio)
    }
    resize()
    window.addEventListener('resize', resize)

    for (let i = 0; i < 60; i++) {
      particles.push({
        x: Math.random() * canvas.offsetWidth,
        y: Math.random() * canvas.offsetHeight,
        r: Math.random() * 1.5 + 0.5,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        alpha: Math.random() * 0.4 + 0.1,
      })
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight)
      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        if (p.x < 0 || p.x > canvas.offsetWidth) p.vx *= -1
        if (p.y < 0 || p.y > canvas.offsetHeight) p.vy *= -1
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(124, 58, 237, ${p.alpha})`
        ctx.fill()
      })

      // draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x
          const dy = particles[i].y - particles[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            ctx.beginPath()
            ctx.moveTo(particles[i].x, particles[i].y)
            ctx.lineTo(particles[j].x, particles[j].y)
            ctx.strokeStyle = `rgba(124, 58, 237, ${0.06 * (1 - dist / 120)})`
            ctx.lineWidth = 0.5
            ctx.stroke()
          }
        }
      }
      animId = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
}

/* ── Feature Card ────────────────────────────────────────────────── */
const features = [
  {
    icon: Map,
    title: 'Developer Landscape',
    desc: 'Explore UMAP-projected clusters of 65K+ developers. See where you fit in the ecosystem.',
    to: '/landscape',
    gradient: 'from-purple-accent/20 to-blue-500/20',
  },
  {
    icon: Brain,
    title: 'Career Analyzer',
    desc: 'Predict churn risk and estimate career value with explainable ML models.',
    to: '/analyzer',
    gradient: 'from-green-500/20 to-teal-500/20',
  },
  {
    icon: TrendingUp,
    title: 'Tech Forecast',
    desc: 'See adoption trends for 20+ technologies with 2-year Prophet-based forecasts.',
    to: '/forecast',
    gradient: 'from-amber-500/20 to-orange-500/20',
  },
  {
    icon: Search,
    title: 'Find My Tribe',
    desc: 'Describe yourself and find your developer cluster plus 5 most similar peers.',
    to: '/tribe',
    gradient: 'from-pink-500/20 to-rose-500/20',
  },
]

/* ── Page ─────────────────────────────────────────────────────────── */
export default function Landing() {
  return (
    <div className="relative">
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <Particles />

        {/* gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-accent/15 rounded-full blur-3xl pointer-events-none pulse-glow" />
        <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none pulse-glow" style={{ animationDelay: '1s' }} />

        <div className="relative z-10 max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            {/* badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-medium text-purple-light mb-8">
              <Sparkles className="w-3.5 h-3.5" />
              Powered by ML · NLP · Clustering
            </div>

            <h1 className="text-5xl sm:text-7xl font-black tracking-tight mb-6">
              <span className="bg-gradient-to-r from-white via-purple-light to-purple-accent bg-clip-text text-transparent">
                DevIntel
              </span>
            </h1>

            <p className="text-xl sm:text-2xl text-text-secondary font-light mb-4">
              End-to-End Developer Intelligence Platform
            </p>

            <p className="text-sm sm:text-base text-text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
              Analyzing <span className="text-text-primary font-medium">65,437</span> developers
              across <span className="text-text-primary font-medium">5 behavioral clusters</span> using
              UMAP dimensionality reduction, XGBoost churn prediction, and Prophet time-series
              forecasting — with full explainability via SHAP values and sentence-transformer embeddings.
            </p>

            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link
                to="/landscape"
                className="group inline-flex items-center gap-2 px-7 py-3.5 rounded-xl animated-gradient text-white font-semibold text-sm shadow-lg shadow-purple-accent/25 hover:shadow-purple-accent/40 transition-shadow"
              >
                Explore the Data
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl glass text-text-primary font-semibold text-sm hover:bg-white/10 transition-colors"
              >
                <Github className="w-4 h-4" /> View Source
              </a>
            </div>
          </motion.div>
        </div>

        {/* scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
        >
          <div className="w-5 h-8 rounded-full border-2 border-text-muted/40 flex justify-center pt-1.5">
            <div className="w-1 h-1.5 rounded-full bg-text-muted/60" />
          </div>
        </motion.div>
      </section>

      {/* ── Stats ────────────────────────────────────────────────── */}
      <section className="relative max-w-6xl mx-auto px-4 -mt-16 z-20 mb-24">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Users} label="Developers" value={65437} subtitle="Survey respondents analyzed" index={0} />
          <StatCard icon={Layers} label="Clusters" value={5} subtitle="Behavioral archetypes" index={1} />
          <StatCard icon={Cpu} label="Technologies" value={20} subtitle="Tracked & forecasted" index={2} />
          <StatCard icon={BarChart3} label="ML Models" value={3} subtitle="XGBoost · Prophet · SBERT" index={3} />
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-14"
        >
          <h2 className="text-3xl font-bold mb-3">Platform Features</h2>
          <p className="text-text-secondary max-w-xl mx-auto">
            Four interactive modules, each powered by a different ML technique.
          </p>
        </motion.div>

        <div className="grid sm:grid-cols-2 gap-5">
          {features.map((f, i) => (
            <motion.div
              key={f.to}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <Link
                to={f.to}
                className="group block p-6 rounded-2xl glass hover:glow-purple-sm transition-all duration-300"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <f.icon className="w-6 h-6 text-text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                  {f.title}
                  <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-60 transition-opacity" />
                </h3>
                <p className="text-sm text-text-secondary leading-relaxed">{f.desc}</p>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="border-t border-dark-border py-8 text-center text-xs text-text-muted">
        <p>
          Built with React · FastAPI · XGBoost · Prophet · SBERT — {' '}
          <span className="text-text-secondary">DevIntel © {new Date().getFullYear()}</span>
        </p>
      </footer>
    </div>
  )
}
