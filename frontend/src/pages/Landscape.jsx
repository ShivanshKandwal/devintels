import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { MapPin, Users, DollarSign, Code, ChevronDown, Info } from 'lucide-react'
import ClusterBadge from '../components/ClusterBadge'
import TechPill from '../components/TechPill'
import {
  umapPoints as demoUmapPoints, clusterProfiles as demoClusterProfiles, CLUSTER_COLORS, CLUSTER_NAMES,
} from '../lib/demoData'
import { getClusters } from '../lib/api'
import { useApi } from '../hooks/useApi'

/* ── Color modes ─────────────────────────────────────────────────── */
const COLOR_MODES = ['Cluster', 'Salary', 'Experience']

function salaryColor(s) {
  const t = Math.min(s / 200000, 1)
  const r = Math.round(16 + t * 200)
  const g = Math.round(185 - t * 120)
  const b = Math.round(129 - t * 80)
  return `rgb(${r},${g},${b})`
}

function expColor(e) {
  const t = Math.min(e / 25, 1)
  const r = Math.round(59 + t * 100)
  const g = Math.round(130 - t * 80)
  const b = Math.round(246 - t * 60)
  return `rgb(${r},${g},${b})`
}

/* ── Custom tooltip ──────────────────────────────────────────────── */
function ScatterTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div className="glass-strong rounded-xl px-4 py-3 text-xs space-y-1 shadow-xl">
      <div className="font-semibold text-text-primary">{CLUSTER_NAMES[d.cluster]}</div>
      <div className="text-text-secondary">Stage: <span className="text-text-primary">{d.stage}</span></div>
      <div className="text-text-secondary">Salary: <span className="text-text-primary">${d.salary?.toLocaleString()}</span></div>
      <div className="text-text-secondary">Language: <span className="text-text-primary">{d.language}</span></div>
      <div className="text-text-secondary">Experience: <span className="text-text-primary">{d.experience} yrs</span></div>
    </div>
  )
}

/* ── Page ─────────────────────────────────────────────────────────── */
export default function Landscape() {
  const { data: clustersData } = useApi(getClusters, {
    points: demoUmapPoints,
    profiles: demoClusterProfiles
  })

  const points = clustersData?.points || demoUmapPoints
  const profiles = clustersData?.profiles || demoClusterProfiles

  const [selectedCluster, setSelectedCluster] = useState(null)
  const [colorMode, setColorMode] = useState('Cluster')
  const [sortCol, setSortCol] = useState('count')
  const [sortDir, setSortDir] = useState('desc')

  const filteredPoints = useMemo(() => {
    if (selectedCluster === null) return points
    return points.filter((p) => p.cluster === selectedCluster)
  }, [selectedCluster, points])

  const pointsByCluster = useMemo(() => {
    const groups = {}
    CLUSTER_NAMES.forEach((_, i) => { groups[i] = [] })
    filteredPoints.forEach((p) => {
      if (!groups[p.cluster]) groups[p.cluster] = []
      groups[p.cluster].push(p)
    })
    return groups
  }, [filteredPoints])

  const getPointColor = (point) => {
    if (colorMode === 'Salary') return salaryColor(point.salary)
    if (colorMode === 'Experience') return expColor(point.experience)
    return CLUSTER_COLORS[point.cluster]
  }

  const sorted = useMemo(() => {
    return [...profiles].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      return (a[sortCol] - b[sortCol]) * dir
    })
  }, [sortCol, sortDir, profiles])

  const toggleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('desc') }
  }

  return (
    <div className="pt-20 pb-16 min-h-screen">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold mb-2">Developer Landscape</h1>
          <p className="text-text-secondary text-sm">
            65,437 developers projected to 2D via UMAP, colored by behavioral cluster.
          </p>
        </motion.div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* ── Left panel — Cluster cards ──────────────────────── */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:w-[30%] space-y-4"
          >
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Clusters</h2>
              {selectedCluster !== null && (
                <button
                  onClick={() => setSelectedCluster(null)}
                  className="text-xs text-purple-accent hover:text-purple-light transition-colors cursor-pointer"
                >
                  Show all
                </button>
              )}
            </div>

            {profiles.map((c) => {
              const active = selectedCluster === c.id
              return (
                <motion.div
                  key={c.id}
                  onClick={() => setSelectedCluster(active ? null : c.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setSelectedCluster(active ? null : c.id);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  whileTap={{ scale: 0.98 }}
                  className={`w-full text-left p-5 rounded-2xl glass transition-all duration-300 cursor-pointer mb-4 hover:scale-[1.01] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-accent/50 ${
                    active ? 'glow-purple border-purple-accent/60 bg-purple-accent/5' : 'border-slate-200/50 hover:bg-black/[0.01]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <ClusterBadge clusterId={c.id} />
                    <span className="text-xs font-semibold font-mono text-text-secondary bg-black/[0.04] px-2.5 py-1 rounded-md">{c.count.toLocaleString()}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs mb-4 text-text-secondary">
                    <div className="flex items-center gap-1.5">
                      <DollarSign className="w-3.5 h-3.5 text-purple-accent" />
                      <span><strong className="text-text-primary text-sm">${(c.avgSalary / 1000).toFixed(0)}K</strong> avg</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Code className="w-3.5 h-3.5 text-purple-accent" />
                      <span><strong className="text-text-primary text-sm">{c.avgExperience}</strong> yrs exp</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-200/50">
                    {c.topTechs.slice(0, 3).map((t) => (
                      <TechPill key={t} name={t} selected={false} className="opacity-90 hover:opacity-100" />
                    ))}
                  </div>
                </motion.div>
              )
            })}
          </motion.div>

          {/* ── Right panel — Scatter plot ──────────────────────── */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:w-[70%]"
          >
            {/* Color mode toggle */}
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xs text-text-muted">Color by:</span>
              {COLOR_MODES.map((m) => (
                <button
                  key={m}
                  onClick={() => setColorMode(m)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    colorMode === m
                      ? 'bg-purple-accent text-white'
                      : 'glass text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>

            <div className="rounded-2xl glass p-4" style={{ minHeight: 500 }}>
              <ResponsiveContainer width="100%" height={480}>
                <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <XAxis type="number" dataKey="x" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <YAxis type="number" dataKey="y" tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ScatterTooltip />} cursor={false} />
                  {Object.entries(pointsByCluster).map(([cId, points]) => (
                    <Scatter key={cId} data={points} isAnimationActive={true} animationDuration={1200}>
                      {points.map((p, i) => (
                        <Cell
                          key={i}
                          fill={getPointColor(p)}
                          fillOpacity={selectedCluster === null || selectedCluster === p.cluster ? 0.7 : 0.1}
                          r={3}
                        />
                      ))}
                    </Scatter>
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            {/* Legend */}
            {colorMode === 'Cluster' && (
              <div className="flex flex-wrap gap-3 mt-4">
                {CLUSTER_NAMES.map((name, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-xs text-text-secondary">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CLUSTER_COLORS[i] }} />
                    {name}
                  </div>
                ))}
              </div>
            )}
            {colorMode === 'Salary' && (
              <div className="flex items-center gap-2 mt-4 text-xs text-text-secondary">
                <span>$40K</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'linear-gradient(90deg, #10b981, #f59e0b, #ef4444)' }} />
                <span>$200K+</span>
              </div>
            )}
            {colorMode === 'Experience' && (
              <div className="flex items-center gap-2 mt-4 text-xs text-text-secondary">
                <span>1 yr</span>
                <div className="flex-1 h-2 rounded-full" style={{ background: 'linear-gradient(90deg, #3b82f6, #a855f7, #ef4444)' }} />
                <span>25+ yrs</span>
              </div>
            )}
          </motion.div>
        </div>

        {/* ── Comparison table ─────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-12"
        >
          <h2 className="text-xl font-bold mb-4">Cluster Comparison</h2>
          <div className="rounded-2xl glass overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200/50 text-text-secondary text-xs uppercase tracking-wider">
                  {[
                    { key: 'name', label: 'Cluster' },
                    { key: 'count', label: 'Size' },
                    { key: 'avgSalary', label: 'Avg Salary' },
                    { key: 'avgExperience', label: 'Avg Exp' },
                    { key: 'satisfaction', label: 'Satisfaction' },
                    { key: 'remoteRatio', label: 'Remote %' },
                    { key: 'churnRate', label: 'Churn Rate' },
                  ].map((col) => (
                    <th
                      key={col.key}
                      onClick={() => col.key !== 'name' && toggleSort(col.key)}
                      className={`px-4 py-3 text-left font-medium ${
                        col.key !== 'name' ? 'cursor-pointer hover:text-text-primary' : ''
                      }`}
                    >
                      <span className="flex items-center gap-1">
                        {col.label}
                        {sortCol === col.key && (
                          <ChevronDown className={`w-3 h-3 transition-transform ${sortDir === 'asc' ? 'rotate-180' : ''}`} />
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((c) => (
                  <tr
                    key={c.id}
                    className="border-b border-slate-200/50 hover:bg-black/[0.01] transition-colors"
                  >
                    <td className="px-4 py-3">
                      <ClusterBadge clusterId={c.id} />
                    </td>
                    <td className="px-4 py-3 text-text-primary">{c.count.toLocaleString()}</td>
                    <td className="px-4 py-3 text-text-primary">${c.avgSalary.toLocaleString()}</td>
                    <td className="px-4 py-3 text-text-primary">{c.avgExperience} yrs</td>
                    <td className="px-4 py-3 text-text-primary">{c.satisfaction}/5</td>
                    <td className="px-4 py-3 text-text-primary">{(c.remoteRatio * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3">
                      <span className={`font-medium ${c.churnRate > 0.2 ? 'text-danger' : c.churnRate > 0.15 ? 'text-warning' : 'text-success'}`}>
                        {(c.churnRate * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center gap-2 mt-3 text-xs text-text-muted">
            <Info className="w-3.5 h-3.5" />
            Click column headers to sort. Cluster sizes represent developer counts from the dataset.
          </div>
        </motion.div>
      </div>
    </div>
  )
}
