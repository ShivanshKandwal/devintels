import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts'
import {
  Sliders, Star, Monitor, Wifi, Building2, Globe, Code, Zap,
  AlertTriangle, TrendingUp, Lightbulb, ChevronRight,
} from 'lucide-react'
import RiskGauge from '../components/RiskGauge'
import ShapWaterfall from '../components/ShapWaterfall'
import ClusterBadge from '../components/ClusterBadge'
import SkeletonLoader from '../components/SkeletonLoader'
import {
  demoChurnResult, demoCareerResult, languages, countries, orgSizes, CLUSTER_COLORS,
} from '../lib/demoData'
import { predictChurn, predictCareer } from '../lib/api'

/* ── Career stage from years ─────────────────────────────────────── */
function getCareerStage(yrs) {
  if (yrs < 2) return 'Junior'
  if (yrs < 5) return 'Mid'
  if (yrs < 10) return 'Senior'
  if (yrs < 15) return 'Staff'
  return 'Principal'
}

/* ── Star rating component ───────────────────────────────────────── */
function StarRating({ value, onChange }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          onClick={() => onChange(n)}
          className="cursor-pointer transition-transform hover:scale-110"
        >
          <Star
            className={`w-6 h-6 ${n <= value ? 'text-warning fill-warning' : 'text-dark-border'}`}
          />
        </button>
      ))}
    </div>
  )
}

/* ── Page ─────────────────────────────────────────────────────────── */
export default function Analyzer() {
  // Form state
  const [yearsCoding, setYearsCoding] = useState(8)
  const [language, setLanguage] = useState('TypeScript')
  const [orgSize, setOrgSize] = useState('201-1,000 employees')
  const [country, setCountry] = useState('United States')
  const [usesAI, setUsesAI] = useState(true)
  const [satisfaction, setSatisfaction] = useState(4)
  const [remoteWork, setRemoteWork] = useState('Remote')

  // Results state
  const [churnResult, setChurnResult] = useState(null)
  const [careerResult, setCareerResult] = useState(null)
  const [loading, setLoading] = useState(null) // 'churn' | 'career' | null
  const [countrySearch, setCountrySearch] = useState('')
  const [showCountryDropdown, setShowCountryDropdown] = useState(false)

  const stage = getCareerStage(yearsCoding)
  const filteredCountries = countries.filter((c) =>
    c.toLowerCase().includes(countrySearch.toLowerCase())
  )

  const buildProfile = () => ({
    years_coding: yearsCoding,
    primary_language: language,
    org_size: orgSize,
    country,
    uses_ai_tools: usesAI,
    job_satisfaction: satisfaction,
    remote_work: remoteWork,
    career_stage: stage,
  })

  const handleChurn = useCallback(async () => {
    setLoading('churn')
    setChurnResult(null)
    try {
      const res = await predictChurn(buildProfile())
      setChurnResult(res.data)
    } catch {
      // Simulate loading delay for demo
      await new Promise((r) => setTimeout(r, 1200))
      setChurnResult(demoChurnResult)
    }
    setLoading(null)
  }, [yearsCoding, language, orgSize, country, usesAI, satisfaction, remoteWork])

  const handleCareer = useCallback(async () => {
    setLoading('career')
    setCareerResult(null)
    try {
      const res = await predictCareer(buildProfile())
      setCareerResult(res.data)
    } catch {
      await new Promise((r) => setTimeout(r, 1200))
      setCareerResult(demoCareerResult)
    }
    setLoading(null)
  }, [yearsCoding, language, orgSize, country, usesAI, satisfaction, remoteWork])

  const selectClasses = 'w-full bg-dark-surface border border-dark-border rounded-xl px-4 py-2.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-purple-accent/50 focus:border-purple-accent/50 transition-all appearance-none cursor-pointer'

  return (
    <div className="pt-32 pb-16 min-h-screen">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Career Analyzer</h1>
          <p className="text-text-secondary text-sm">
            Predict your churn risk and estimate career value using explainable ML models.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* ── Left: Input Form ──────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="rounded-2xl glass p-6 space-y-6">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Sliders className="w-5 h-5 text-purple-accent" />
                Developer Profile
              </h2>

              {/* Years Coding */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Years Coding
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min={0}
                    max={30}
                    value={yearsCoding}
                    onChange={(e) => setYearsCoding(+e.target.value)}
                    className="flex-1 accent-purple-accent cursor-pointer"
                  />
                  <span className="w-12 text-center text-lg font-bold text-purple-accent">
                    {yearsCoding}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-text-muted mt-1">
                  <span>0</span><span>30</span>
                </div>
              </div>

              {/* Primary Language */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  <Code className="w-4 h-4 inline mr-1" />Primary Language
                </label>
                <select value={language} onChange={(e) => setLanguage(e.target.value)} className={selectClasses}>
                  {languages.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>

              {/* Org Size */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  <Building2 className="w-4 h-4 inline mr-1" />Organization Size
                </label>
                <select value={orgSize} onChange={(e) => setOrgSize(e.target.value)} className={selectClasses}>
                  {orgSizes.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              </div>

              {/* Country */}
              <div className="relative">
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  <Globe className="w-4 h-4 inline mr-1" />Country
                </label>
                <input
                  type="text"
                  value={showCountryDropdown ? countrySearch : country}
                  onFocus={() => { setShowCountryDropdown(true); setCountrySearch('') }}
                  onBlur={() => setTimeout(() => setShowCountryDropdown(false), 200)}
                  onChange={(e) => setCountrySearch(e.target.value)}
                  placeholder="Search country..."
                  className={selectClasses}
                />
                {showCountryDropdown && (
                  <div className="absolute z-20 w-full mt-1 max-h-48 overflow-y-auto rounded-xl glass-strong shadow-xl">
                    {filteredCountries.map((c) => (
                      <button
                        key={c}
                        onMouseDown={() => { setCountry(c); setShowCountryDropdown(false) }}
                        className="w-full text-left px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-white/5 cursor-pointer"
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* AI Tools Toggle */}
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-text-secondary flex items-center gap-2">
                  <Zap className="w-4 h-4" />Uses AI Tools
                </label>
                <button
                  onClick={() => setUsesAI(!usesAI)}
                  className={`relative w-12 h-6 rounded-full transition-colors cursor-pointer ${
                    usesAI ? 'bg-purple-accent' : 'bg-dark-border'
                  }`}
                >
                  <span
                    className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
                      usesAI ? 'translate-x-6' : ''
                    }`}
                  />
                </button>
              </div>

              {/* Job Satisfaction */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Job Satisfaction
                </label>
                <StarRating value={satisfaction} onChange={setSatisfaction} />
              </div>

              {/* Remote Work */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  <Wifi className="w-4 h-4 inline mr-1" />Work Mode
                </label>
                <div className="flex gap-2">
                  {['Remote', 'Hybrid', 'In-office'].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setRemoteWork(mode)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                        remoteWork === mode
                          ? 'bg-purple-accent text-white'
                          : 'glass text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>

              {/* Career Stage Badge */}
              <div className="flex items-center gap-3 p-3 rounded-xl bg-dark-surface">
                <Monitor className="w-4 h-4 text-purple-accent" />
                <span className="text-sm text-text-secondary">Career Stage:</span>
                <span className="text-sm font-semibold text-purple-accent">{stage}</span>
              </div>

              {/* Buttons */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleChurn}
                  disabled={loading !== null}
                  className="py-3 rounded-xl bg-purple-accent text-white text-sm font-semibold hover:bg-purple-dark transition-colors disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
                >
                  <AlertTriangle className="w-4 h-4" />
                  Predict Churn
                </button>
                <button
                  onClick={handleCareer}
                  disabled={loading !== null}
                  className="py-3 rounded-xl glass text-text-primary text-sm font-semibold hover:bg-white/10 transition-colors disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
                >
                  <TrendingUp className="w-4 h-4" />
                  Estimate Value
                </button>
              </div>
            </div>
          </motion.div>

          {/* ── Right: Results ────────────────────────────────── */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* Loading states */}
            {loading === 'churn' && (
              <div className="space-y-4">
                <SkeletonLoader variant="card" />
                <SkeletonLoader variant="chart" />
              </div>
            )}
            {loading === 'career' && (
              <div className="space-y-4">
                <SkeletonLoader variant="card" />
                <SkeletonLoader variant="chart" />
              </div>
            )}

            {/* Empty state */}
            {!loading && !churnResult && !careerResult && (
              <div className="rounded-2xl glass p-12 text-center">
                <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-purple-accent/10 flex items-center justify-center">
                  <Lightbulb className="w-10 h-10 text-purple-accent/60" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-text-primary">
                  Configure & Predict
                </h3>
                <p className="text-sm text-text-secondary max-w-sm mx-auto">
                  Fill in your developer profile on the left and click a prediction button to see ML-powered insights about your career.
                </p>
              </div>
            )}

            {/* ── Churn Result ──────────────────────────────── */}
            <AnimatePresence>
              {churnResult && !loading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  <div className="rounded-2xl glass p-6">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-warning" />
                      Churn Risk Analysis
                    </h3>
                    <div className="flex flex-col sm:flex-row items-center gap-6">
                      <RiskGauge probability={churnResult.churn_probability} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-sm text-text-secondary">Risk Tier:</span>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                            churnResult.risk_tier === 'Low' ? 'bg-success/20 text-success' :
                            churnResult.risk_tier === 'Medium' ? 'bg-warning/20 text-warning' :
                            'bg-danger/20 text-danger'
                          }`}>
                            {churnResult.risk_tier}
                          </span>
                        </div>
                        <h4 className="text-sm font-medium text-text-secondary mb-3">Feature Importance (SHAP)</h4>
                        <ShapWaterfall values={churnResult.shap_values} />
                      </div>
                    </div>
                  </div>

                  {/* Recommendations */}
                  {churnResult.recommendations && (
                    <div className="rounded-2xl glass p-6">
                      <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4 text-purple-accent" />
                        Recommendations
                      </h4>
                      <ul className="space-y-2">
                        {churnResult.recommendations.map((r, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                            <ChevronRight className="w-4 h-4 text-purple-accent flex-shrink-0 mt-0.5" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Career Result ─────────────────────────────── */}
            <AnimatePresence>
              {careerResult && !loading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  <div className="rounded-2xl glass p-6">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-success" />
                      Career Valuation
                    </h3>

                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="p-4 rounded-xl bg-dark-surface text-center">
                        <div className="text-2xl font-bold text-success">
                          ${(careerResult.predicted_salary / 1000).toFixed(0)}K
                        </div>
                        <div className="text-xs text-text-muted mt-1">Predicted Salary</div>
                      </div>
                      <div className="p-4 rounded-xl bg-dark-surface text-center">
                        <div className="text-2xl font-bold text-purple-accent">
                          {careerResult.percentile}th
                        </div>
                        <div className="text-xs text-text-muted mt-1">Percentile</div>
                      </div>
                      <div className="p-4 rounded-xl bg-dark-surface text-center">
                        <ClusterBadge clusterId={careerResult.predicted_cluster} />
                        <div className="text-xs text-text-muted mt-2">Your Cluster</div>
                      </div>
                    </div>

                    <div className="text-sm text-text-secondary mb-2">
                      Salary range: <span className="text-text-primary font-medium">
                        ${(careerResult.salary_range[0] / 1000).toFixed(0)}K – ${(careerResult.salary_range[1] / 1000).toFixed(0)}K
                      </span>
                    </div>
                  </div>

                  {/* Comparison chart */}
                  <div className="rounded-2xl glass p-6">
                    <h4 className="text-sm font-semibold mb-4">Your Salary vs Cluster Averages</h4>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={careerResult.comparison} barGap={4}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a33" vertical={false} />
                        <XAxis
                          dataKey="cluster"
                          tick={{ fontSize: 10, fill: '#6b7280' }}
                          axisLine={false}
                          tickLine={false}
                          interval={0}
                          angle={-15}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                        <Tooltip
                          contentStyle={{ background: '#1a1a1f', border: '1px solid #2a2a33', borderRadius: '12px', fontSize: 12 }}
                          labelStyle={{ color: '#f0f0f5' }}
                        />
                        <Bar dataKey="salary" name="Cluster Avg" radius={[6, 6, 0, 0]} isAnimationActive animationDuration={800}>
                          {careerResult.comparison.map((_, i) => (
                            <Cell key={i} fill={CLUSTER_COLORS[i]} fillOpacity={0.5} />
                          ))}
                        </Bar>
                        <Bar dataKey="yours" name="Your Estimate" fill="#7c3aed" radius={[6, 6, 0, 0]} isAnimationActive animationDuration={800} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
