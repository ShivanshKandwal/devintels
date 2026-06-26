import { CLUSTER_COLORS, CLUSTER_NAMES } from '../lib/demoData'

export default function ClusterBadge({ clusterId, name, className = '' }) {
  const color = CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length]
  const label = name || CLUSTER_NAMES[clusterId] || `Cluster ${clusterId}`

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${className}`}
      style={{
        background: `linear-gradient(135deg, ${color}22, ${color}11)`,
        color: color,
        border: `1px solid ${color}33`,
      }}
    >
      <span
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      {label}
    </span>
  )
}
