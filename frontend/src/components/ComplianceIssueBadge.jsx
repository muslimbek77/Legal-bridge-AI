import clsx from 'clsx'

const severityConfig = {
  critical: { 
    label: 'Kritik', 
    color: 'bg-red-100 text-red-800 border-red-200',
    icon: '🔴'
  },
  high: { 
    label: 'Yuqori', 
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: '🟠'
  },
  major: { 
    label: 'Jiddiy', 
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: '🟠'
  },
  medium: { 
    label: 'O\'rta', 
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    icon: '🟡'
  },
  minor: { 
    label: 'Kichik', 
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    icon: '🟡'
  },
  low: { 
    label: 'Past', 
    color: 'bg-green-100 text-green-800 border-green-200',
    icon: '🟢'
  },
  info: { 
    label: 'Ma\'lumot', 
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    icon: '🔵'
  },
}

export default function ComplianceIssueBadge({ severity, showIcon = true }) {
  const config = severityConfig[severity] || severityConfig.info

  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
      config.color
    )}>
      {showIcon && <span className="mr-1">{config.icon}</span>}
      {config.label}
    </span>
  )
}
