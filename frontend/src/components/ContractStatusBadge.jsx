import clsx from 'clsx'

const statusConfig = {
  draft: { label: 'Qoralama', color: 'bg-gray-100 text-gray-800' },
  pending: { label: 'Kutilmoqda', color: 'bg-yellow-100 text-yellow-800' },
  processing: { label: 'Tahlil qilinmoqda', color: 'bg-blue-100 text-blue-800' },
  analyzed: { label: 'Tahlil qilindi', color: 'bg-green-100 text-green-800' },
  approved: { label: 'Tasdiqlandi', color: 'bg-emerald-100 text-emerald-800' },
  rejected: { label: 'Rad etildi', color: 'bg-red-100 text-red-800' },
  archived: { label: 'Arxivlandi', color: 'bg-purple-100 text-purple-800' },
}

export default function ContractStatusBadge({ status }) {
  const config = statusConfig[status] || statusConfig.draft

  return (
    <span className={clsx(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      config.color
    )}>
      {config.label}
    </span>
  )
}
