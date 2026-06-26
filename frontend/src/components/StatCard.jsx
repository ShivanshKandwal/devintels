import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

export default function StatCard({ icon: Icon, label, value, subtitle, index = 0 }) {
  const [display, setDisplay] = useState(0)
  const ref = useRef(null)
  const hasAnimated = useRef(false)

  useEffect(() => {
    const numeric = typeof value === 'number' ? value : parseInt(String(value).replace(/[^0-9]/g, ''), 10)
    if (isNaN(numeric)) {
      setDisplay(value)
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          const duration = 1800
          const start = performance.now()
          const tick = (now) => {
            const progress = Math.min((now - start) / duration, 1)
            const eased = 1 - Math.pow(1 - progress, 3)
            setDisplay(Math.floor(eased * numeric))
            if (progress < 1) requestAnimationFrame(tick)
          }
          requestAnimationFrame(tick)
        }
      },
      { threshold: 0.3 }
    )

    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [value])

  const formatNumber = (n) => {
    if (typeof n === 'string') return n
    return n >= 1000 ? n.toLocaleString() : n
  }

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="group relative rounded-2xl p-8 glass hover:glow-purple-sm transition-all duration-300 cursor-default"
    >
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="relative">
        <div className="flex items-center gap-4 mb-4">
          {Icon && (
            <div className="w-12 h-12 rounded-xl bg-purple-accent/10 flex items-center justify-center text-purple-accent group-hover:bg-purple-accent/20 transition-colors">
              <Icon className="w-6 h-6" />
            </div>
          )}
          <span className="text-base font-semibold text-text-secondary">{label}</span>
        </div>
        <div className="text-4xl font-black text-text-primary tracking-tight">
          {formatNumber(display)}
        </div>
        {subtitle && (
          <p className="mt-2 text-sm text-text-muted">{subtitle}</p>
        )}
      </div>
    </motion.div>
  )
}
