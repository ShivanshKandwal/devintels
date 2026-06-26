import { useState, useEffect } from 'react'
import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts'
import { motion } from 'framer-motion'

function getColor(pct) {
  if (pct <= 33) return '#10b981'
  if (pct <= 66) return '#f59e0b'
  return '#ef4444'
}

function getTier(pct) {
  if (pct <= 33) return 'Low'
  if (pct <= 66) return 'Medium'
  return 'High'
}

export default function RiskGauge({ probability = 0, size = 220 }) {
  const [animatedValue, setAnimatedValue] = useState(0)
  const pct = Math.round(probability * 100)
  const color = getColor(pct)
  const tier = getTier(pct)

  useEffect(() => {
    const duration = 1200
    const start = performance.now()
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setAnimatedValue(eased * pct)
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [pct])

  const data = [{ value: animatedValue, fill: color }]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="relative flex flex-col items-center"
    >
      <RadialBarChart
        width={size}
        height={size}
        cx={size / 2}
        cy={size / 2}
        innerRadius={size * 0.33}
        outerRadius={size * 0.45}
        startAngle={225}
        endAngle={-45}
        data={data}
        barSize={12}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} tick={false} angleAxisId={0} />
        <RadialBar
          dataKey="value"
          cornerRadius={6}
          background={{ fill: '#1a1a1f' }}
          angleAxisId={0}
        />
      </RadialBarChart>

      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold" style={{ color }}>
          {Math.round(animatedValue)}%
        </span>
        <span className="text-xs font-medium text-text-secondary mt-1">
          {tier} Risk
        </span>
      </div>
    </motion.div>
  )
}
