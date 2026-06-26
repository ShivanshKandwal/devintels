export default function SkeletonLoader({ height = 'h-4', width = 'w-full', variant = 'text', className = '' }) {
  const base = 'animate-pulse rounded bg-dark-border/50'

  if (variant === 'card') {
    return (
      <div className={`${base} rounded-2xl p-6 space-y-4 ${className}`} style={{ minHeight: 160 }}>
        <div className="h-4 w-1/3 rounded bg-dark-border/70" />
        <div className="h-8 w-1/2 rounded bg-dark-border/70" />
        <div className="h-3 w-2/3 rounded bg-dark-border/70" />
      </div>
    )
  }

  if (variant === 'chart') {
    return (
      <div className={`${base} rounded-2xl ${className}`} style={{ minHeight: 300 }}>
        <div className="flex items-end gap-2 p-6 h-full">
          {[40, 65, 50, 80, 55, 70, 45, 75, 60].map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-t bg-dark-border/70"
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
      </div>
    )
  }

  // text variant
  return <div className={`${base} ${height} ${width} ${className}`} />
}
