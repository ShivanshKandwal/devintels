import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, Users, Globe, Code, DollarSign, Sparkles, ChevronRight, BarChart3,
} from 'lucide-react'
import ClusterBadge from '../components/ClusterBadge'
import { demoSimilarDevs, CLUSTER_COLORS, CLUSTER_NAMES } from '../lib/demoData'
import { searchSimilar } from '../lib/api'
import SkeletonLoader from '../components/SkeletonLoader'

/* ── Page ─────────────────────────────────────────────────────────── */
export default function Tribe() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await searchSimilar(query)
      setResult(res.data)
    } catch {
      await new Promise((r) => setTimeout(r, 1400))
      setResult(demoSimilarDevs)
    }
    setLoading(false)
  }, [query])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <div className="pt-32 pb-16 min-h-screen">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-medium text-purple-light mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            Powered by Sentence Transformers
          </div>
          <h1 className="text-3xl font-bold mb-2">Find My Tribe</h1>
          <p className="text-text-secondary text-sm max-w-lg mx-auto">
            Describe yourself as a developer and we'll find your behavioral cluster plus the 5 most similar developers in our dataset.
          </p>
        </motion.div>

        {/* Search box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-10"
        >
          <div className="rounded-2xl glass p-6">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={4}
              placeholder="I'm a senior full-stack developer with 8 years of experience, primarily working with TypeScript, React, and Node.js. I work remotely for a mid-size startup and recently started using AI coding tools like GitHub Copilot..."
              className="w-full bg-dark-surface border border-dark-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder-text-muted/50 resize-none focus:outline-none focus:ring-2 focus:ring-purple-accent/50 focus:border-purple-accent/50 transition-all"
            />
            <div className="flex items-center justify-between mt-4">
              <span className="text-xs text-text-muted">
                {query.length > 0 ? `${query.split(/\s+/).filter(Boolean).length} words` : 'Describe your tech stack, experience, work style...'}
              </span>
              <button
                onClick={handleSearch}
                disabled={loading || !query.trim()}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-purple-accent text-white text-sm font-semibold hover:bg-purple-dark transition-colors disabled:opacity-50 cursor-pointer"
              >
                <Search className="w-4 h-4" />
                Find My Tribe
              </button>
            </div>
          </div>
        </motion.div>

        {/* Loading */}
        {loading && (
          <div className="space-y-4">
            <SkeletonLoader variant="card" />
            <SkeletonLoader variant="card" />
          </div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Your cluster */}
              <div className="rounded-2xl glass p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Users className="w-5 h-5 text-purple-accent" />
                  <h2 className="text-lg font-semibold">Your Developer Cluster</h2>
                </div>

                <div className="flex flex-col sm:flex-row items-start gap-6">
                  <div className="flex-1">
                    <ClusterBadge
                      clusterId={result.your_cluster.id}
                      className="text-sm mb-3"
                    />
                    <p className="text-sm text-text-secondary leading-relaxed mb-4">
                      {result.your_cluster.description}
                    </p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-text-muted">Match Score:</span>
                      <div className="flex-1 max-w-[200px] h-2 bg-dark-border rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${result.your_cluster.match_score * 100}%` }}
                          transition={{ duration: 1, delay: 0.3 }}
                          className="h-full rounded-full bg-purple-accent"
                        />
                      </div>
                      <span className="text-sm font-bold text-purple-accent">
                        {(result.your_cluster.match_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Cluster similarity bars */}
              <div className="rounded-2xl glass p-6">
                <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-accent" />
                  Similarity to Each Cluster
                </h3>
                <div className="space-y-3">
                  {result.cluster_scores.map((cs, i) => (
                    <div key={cs.name} className="flex items-center gap-3">
                      <span className="text-xs text-text-secondary w-40 truncate">{cs.name}</span>
                      <div className="flex-1 h-3 bg-dark-border rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${cs.score * 100}%` }}
                          transition={{ duration: 0.8, delay: i * 0.1 }}
                          className="h-full rounded-full"
                          style={{ backgroundColor: CLUSTER_COLORS[i] }}
                        />
                      </div>
                      <span className="text-xs font-mono text-text-muted w-10 text-right">
                        {(cs.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Similar developers */}
              <div className="rounded-2xl glass p-6">
                <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                  <Users className="w-4 h-4 text-purple-accent" />
                  5 Most Similar Developers
                </h3>
                <div className="space-y-3">
                  {result.similar_developers.map((dev, i) => (
                    <motion.div
                      key={dev.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + i * 0.1 }}
                      className="flex items-center gap-4 p-4 rounded-xl bg-dark-surface hover:bg-white/[0.03] transition-colors"
                    >
                      {/* Rank */}
                      <div className="w-8 h-8 rounded-lg bg-purple-accent/10 flex items-center justify-center text-sm font-bold text-purple-accent flex-shrink-0">
                        #{i + 1}
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-text-primary">{dev.id}</span>
                          <span className="px-2 py-0.5 rounded-full bg-purple-accent/10 text-purple-accent text-xs font-medium">
                            {dev.stage}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-text-secondary">
                          <span className="flex items-center gap-1">
                            <Globe className="w-3 h-3" />{dev.country}
                          </span>
                          <span className="flex items-center gap-1">
                            <Code className="w-3 h-3" />{dev.language}
                          </span>
                          <span className="flex items-center gap-1">
                            <DollarSign className="w-3 h-3" />{dev.salary_range}
                          </span>
                        </div>
                      </div>

                      {/* Similarity */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <div className="w-20 h-2 bg-dark-border rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${dev.similarity * 100}%` }}
                            transition={{ duration: 0.8, delay: 0.5 + i * 0.1 }}
                            className="h-full rounded-full bg-purple-accent"
                          />
                        </div>
                        <span className="text-xs font-mono text-purple-accent w-10 text-right">
                          {(dev.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty state when no results yet */}
        {!loading && !result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center py-16"
          >
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-purple-accent/10 flex items-center justify-center">
              <Search className="w-10 h-10 text-purple-accent/40" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              Describe Yourself
            </h3>
            <p className="text-sm text-text-secondary max-w-md mx-auto">
              Write a short paragraph about your tech stack, experience, and working style.
              Our sentence-transformer model will find your tribe.
            </p>
          </motion.div>
        )}
      </div>
    </div>
  )
}
