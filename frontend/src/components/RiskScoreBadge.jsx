import clsx from 'clsx'

export default function RiskScoreBadge({ score, showLabel = true, size = 'md' }) {
  const getRiskLevel = (score) => {
    if (score < 25) return { level: 'low', label: 'Past', color: 'risk-score-low' }
    if (score < 50) return { level: 'medium', label: "O'rta", color: 'risk-score-medium' }
    if (score < 75) return { level: 'high', label: 'Yuqori', color: 'risk-score-high' }
    return { level: 'critical', label: 'Kritik', color: 'risk-score-critical' }
  }

  const { level, label, color } = getRiskLevel(score)

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2',
  }

  const scoreSizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-4xl',
  }

  return (
    <div className={clsx('inline-flex items-center rounded-lg', color, sizeClasses[size])}>
      <span className={clsx('font-bold', scoreSizeClasses[size])}>{score}</span>
      {showLabel && (
        <span className="ml-2 font-medium">
          / 100 ({label} risk)
        </span>
      )}
    </div>
  )
}

export function RiskScoreCircle({ score, size = 120 }) {
  const getRiskColor = (score) => {
    if (score < 25) return '#10B981' // green
    if (score < 50) return '#F59E0B' // yellow
    if (score < 75) return '#F97316' // orange
    return '#EF4444' // red
  }

  const color = getRiskColor(score)
  const circumference = 2 * Math.PI * 40
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size} viewBox="0 0 100 100">
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r="40"
          stroke="#E5E7EB"
          strokeWidth="8"
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx="50"
          cy="50"
          r="40"
          stroke={color}
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-gray-900">{score}</span>
      </div>
    </div>
  )
}
