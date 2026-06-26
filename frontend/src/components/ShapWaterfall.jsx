import { motion } from 'framer-motion'

export default function ShapWaterfall({ values = [] }) {
  if (!values.length) return null

  const sorted = [...values].sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  const maxAbs = Math.max(...sorted.map((v) => Math.abs(v.value)), 0.01)

  return (
    <div className="space-y-2">
      {sorted.map((item, i) => {
        const isPositive = item.value >= 0
        const width = (Math.abs(item.value) / maxAbs) * 100

        return (
          <motion.div
            key={item.feature}
            initial={{ opacity: 0, x: isPositive ? 30 : -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: i * 0.06 }}
            className="flex items-center gap-3"
          >
            <span className="text-xs text-text-secondary w-36 text-right flex-shrink-0 truncate">
              {item.feature}
            </span>
            <div className="flex-1 flex items-center h-6">
              {!isPositive && (
                <div className="flex-1 flex justify-end">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${width}%` }}
                    transition={{ duration: 0.6, delay: i * 0.06 }}
                    className="h-5 rounded-l-md"
                    style={{
                      background: 'linear-gradient(90deg, #10b981, #34d399)',
                    }}
                  />
                </div>
              )}
              <div className="w-px h-6 bg-dark-border flex-shrink-0" />
              {isPositive && (
                <div className="flex-1">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${width}%` }}
                    transition={{ duration: 0.6, delay: i * 0.06 }}
                    className="h-5 rounded-r-md"
                    style={{
                      background: 'linear-gradient(90deg, #f87171, #ef4444)',
                    }}
                  />
                </div>
              )}
            </div>
            <span className="text-xs font-mono w-14 text-right flex-shrink-0" style={{ color: isPositive ? '#ef4444' : '#10b981' }}>
              {isPositive ? '+' : ''}{item.value.toFixed(2)}
            </span>
          </motion.div>
        )
      })}

      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-dark-border">
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <div className="w-3 h-3 rounded-sm" style={{ background: '#10b981' }} />
          Reduces Risk
        </div>
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <div className="w-3 h-3 rounded-sm" style={{ background: '#ef4444' }} />
          Increases Risk
        </div>
      </div>
    </div>
  )
}
