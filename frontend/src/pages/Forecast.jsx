import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Area, ReferenceLine, ReferenceArea,
} from 'recharts'
import { TrendingUp, TrendingDown, ArrowUp, ArrowDown, Info } from 'lucide-react'
import TechPill from '../components/TechPill'
import { forecastData as demoForecastData, techCategories, TECH_COLORS } from '../lib/demoData'
import { getForecast } from '../lib/api'
import { useEffect } from 'react'
import { useDemoMode } from '../context/DemoModeContext'

/* ── Custom chart tooltip ────────────────────────────────────────── */
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-strong rounded-xl px-4 py-3 shadow-xl text-xs space-y-1 min-w-[140px]">
      <div className="font-semibold text-text-primary mb-2">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
            {p.name}
          </span>
          <span className="font-mono text-text-primary">{p.value?.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  )
}

/* ── Page ─────────────────────────────────────────────────────────── */
export default function Forecast() {
  const [activeCategory, setActiveCategory] = useState('Languages')
  const [selectedTechs, setSelectedTechs] = useState(['Python', 'JavaScript', 'TypeScript', 'Rust'])
  const [loadedForecasts, setLoadedForecasts] = useState(demoForecastData)
  const [queriedTechs, setQueriedTechs] = useState([])
  const { demoMode } = useDemoMode()

  const categories = Object.keys(techCategories)

  const toggleTech = (tech) => {
    setSelectedTechs((prev) =>
      prev.includes(tech) ? prev.filter((t) => t !== tech) : [...prev, tech]
    )
  }

  // Reset queried techs when demoMode changes to reload from the correct source
  useEffect(() => {
    setQueriedTechs([])
  }, [demoMode])

  // Fetch forecast from API or use demo data depending on Demo Mode
  useEffect(() => {
    selectedTechs.forEach((tech) => {
      if (!queriedTechs.includes(tech)) {
        setQueriedTechs((prev) => [...prev, tech])
        if (demoMode) {
          setLoadedForecasts((prev) => ({
            ...prev,
            [tech]: demoForecastData[tech],
          }))
        } else {
          getForecast(tech)
            .then((res) => {
              setLoadedForecasts((prev) => ({
                ...prev,
                [tech]: res.data.forecast,
              }))
            })
            .catch((err) => {
              console.warn(`Failed to fetch forecast for ${tech}, using demo data.`, err.message)
              setLoadedForecasts((prev) => ({
                ...prev,
                [tech]: demoForecastData[tech],
              }))
            })
        }
      }
    })
  }, [selectedTechs, queriedTechs, demoMode])

  // Merge data for chart: { year, Python, JavaScript, ... }
  const chartData = useMemo(() => {
    const years = [2022, 2023, 2024, 2025, 2026]
    return years.map((year) => {
      const entry = { year }
      selectedTechs.forEach((tech) => {
        const techPoints = loadedForecasts[tech]
        if (!techPoints) return
        const point = techPoints.find((p) => p.year === year)
        if (point) {
          entry[tech] = point.adoption
          entry[`${tech}_low`] = point.low
          entry[`${tech}_high`] = point.high
          entry[`${tech}_forecast`] = point.isForecast
        }
      })
      return entry
    })
  }, [selectedTechs, loadedForecasts])

  // Rising & Falling
  const trends = useMemo(() => {
    const all = Object.entries(loadedForecasts).map(([name, pts]) => {
      const v2024 = pts.find((p) => p.year === 2024)?.adoption || 0
      const v2026 = pts.find((p) => p.year === 2026)?.adoption || 0
      return { name, val2024: v2024, val2026: v2026, change: v2026 - v2024 }
    })
    all.sort((a, b) => b.change - a.change)
    return {
      rising: all.filter((t) => t.change > 0).slice(0, 6),
      falling: all.filter((t) => t.change < 0).slice(0, 6),
    }
  }, [loadedForecasts])

  return (
    <div className="space-y-8 w-full text-left pb-16">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Technology Forecast</h1>
          <p className="text-text-secondary text-sm">
            Adoption trends for 30 technologies with 2-year Prophet-based forecasts.
          </p>
        </motion.div>

        {/* Category tabs */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-wrap gap-2 mb-4"
        >
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
                activeCategory === cat
                  ? 'bg-purple-accent text-white'
                  : 'glass text-text-secondary hover:text-text-primary'
              }`}
            >
              {cat}
            </button>
          ))}
        </motion.div>

        {/* Tech pills */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="flex flex-wrap gap-2 mb-8"
        >
          {techCategories[activeCategory]?.map((tech) => (
            <TechPill
              key={tech}
              name={tech}
              selected={selectedTechs.includes(tech)}
              onClick={() => toggleTech(tech)}
            />
          ))}
        </motion.div>

        {/* ── Line Chart ─────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl glass p-6 mb-10"
        >
          {selectedTechs.length === 0 ? (
            <div className="flex items-center justify-center h-[400px] text-text-muted text-sm">
              Select at least one technology to display the chart
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={420}>
              <LineChart data={chartData} margin={{ top: 10, right: 30, bottom: 10, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="year"
                  tick={{ fontSize: 12, fill: '#475569' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#475569' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 'auto']}
                  unit="%"
                />
                <Tooltip content={<ChartTooltip />} />

                {/* Forecast shading */}
                <ReferenceArea x1={2024} x2={2026} fill="#7c3aed" fillOpacity={0.04} />
                <ReferenceLine
                  x={2024}
                  stroke="#7c3aed"
                  strokeDasharray="6 4"
                  strokeOpacity={0.5}
                  label={{
                    value: 'Forecast →',
                    position: 'insideTopRight',
                    fill: '#7c3aed',
                    fontSize: 11,
                    fontWeight: 600,
                  }}
                />

                {/* Confidence bands for forecast */}
                {selectedTechs.map((tech) => {
                  const color = TECH_COLORS[tech] || '#7c3aed'
                  return (
                    <Area
                      key={`${tech}_band`}
                      dataKey={`${tech}_high`}
                      stroke="none"
                      fill={color}
                      fillOpacity={0.08}
                      connectNulls={false}
                      isAnimationActive={false}
                      dot={false}
                      activeDot={false}
                      legendType="none"
                      tooltipType="none"
                    />
                  )
                })}

                {selectedTechs.map((tech) => {
                  const color = TECH_COLORS[tech] || '#7c3aed'
                  return (
                    <Line
                      key={tech}
                      type="monotone"
                      dataKey={tech}
                      name={tech}
                      stroke={color}
                      strokeWidth={2.5}
                      dot={{ r: 4, fill: color, strokeWidth: 0 }}
                      activeDot={{ r: 6, strokeWidth: 2, stroke: '#ffffff' }}
                      isAnimationActive={true}
                      animationDuration={1200}
                      connectNulls
                    />
                  )
                })}
              </LineChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        {/* ── Rising / Falling ───────────────────────────────── */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Rising */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <div className="rounded-2xl glass p-6 border-l-4 border-success">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-success" />
                Rising Technologies
              </h3>
              <div className="space-y-3">
                {trends.rising.map((t) => (
                  <div key={t.name} className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-text-primary">{t.name}</span>
                      <div className="text-xs text-text-muted">
                        {t.val2024.toFixed(1)}% → {t.val2026.toFixed(1)}%
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1 text-sm font-bold text-success">
                      <ArrowUp className="w-3.5 h-3.5" />
                      +{t.change.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Falling */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            <div className="rounded-2xl glass p-6 border-l-4 border-danger">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-danger" />
                Declining Technologies
              </h3>
              <div className="space-y-3">
                {trends.falling.map((t) => (
                  <div key={t.name} className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-text-primary">{t.name}</span>
                      <div className="text-xs text-text-muted">
                        {t.val2024.toFixed(1)}% → {t.val2026.toFixed(1)}%
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1 text-sm font-bold text-danger">
                      <ArrowDown className="w-3.5 h-3.5" />
                      {t.change.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        <div className="flex items-center gap-2 mt-6 text-xs text-text-muted">
          <Info className="w-3.5 h-3.5" />
          Forecasts (2025–2026) generated using Prophet time-series models. Shaded region indicates confidence interval.
        </div>
    </div>
  )
}
