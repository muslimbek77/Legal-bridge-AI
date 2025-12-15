import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  DocumentMagnifyingGlassIcon,
} from '@heroicons/react/24/outline'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'
import ComplianceIssueBadge from '../components/ComplianceIssueBadge'
import analysisService from '../services/analysis'

const COLORS = ['#EF4444', '#F97316', '#F59E0B', '#3B82F6']

export default function AnalysisPage() {
  const [severityFilter, setSeverityFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  // Issues ro'yxati
  const { data: issues, isLoading } = useQuery({
    queryKey: ['compliance-issues', severityFilter, statusFilter, searchTerm],
    queryFn: () => analysisService.getComplianceIssues({
      severity: severityFilter,
      is_resolved: statusFilter,
      search: searchTerm,
    }),
  })

  // Statistics API'dan ma'lumot olish
  const { data: statistics } = useQuery({
    queryKey: ['analysis-statistics'],
    queryFn: () => analysisService.getStatistics(),
  })

  // Haqiqiy ma'lumotlarni hisoblash
  const issuesList = issues?.results || []
  const hasIssues = issuesList.length > 0

  // API'dan kelgan statistika
  const stats = {
    critical_count: statistics?.by_severity?.critical || 0,
    high_count: statistics?.by_severity?.high || 0,
    medium_count: statistics?.by_severity?.medium || 0,
    low_count: statistics?.by_severity?.low || 0,
    info_count: statistics?.by_severity?.info || 0,
    resolved_count: statistics?.resolved || 0,
  }

  // Bo'sh holatdagi ma'lumotlar
  const emptyStats = {
    severity_distribution: [
      { name: 'Kritik', value: 0, color: '#EF4444' },
      { name: 'Yuqori', value: 0, color: '#F97316' },
      { name: 'O\'rta', value: 0, color: '#F59E0B' },
      { name: 'Past', value: 0, color: '#10B981' },
      { name: 'Ma\'lumot', value: 0, color: '#3B82F6' },
    ],
    monthly_trend: [
      { month: 'Yan', critical: 0, high: 0, medium: 0 },
      { month: 'Fev', critical: 0, high: 0, medium: 0 },
      { month: 'Mar', critical: 0, high: 0, medium: 0 },
      { month: 'Apr', critical: 0, high: 0, medium: 0 },
      { month: 'May', critical: 0, high: 0, medium: 0 },
      { month: 'Iyun', critical: 0, high: 0, medium: 0 },
    ],
  }

  // Haqiqiy severity distribution
  const severityDistribution = [
    { name: 'Kritik', value: stats.critical_count, color: '#EF4444' },
    { name: 'Yuqori', value: stats.high_count, color: '#F97316' },
    { name: 'O\'rta', value: stats.medium_count, color: '#F59E0B' },
    { name: 'Past', value: stats.low_count, color: '#10B981' },
    { name: 'Ma\'lumot', value: stats.info_count, color: '#3B82F6' },
  ]

  // Oylik trend - API'dan yoki bo'sh
  const monthlyTrend = statistics?.monthly_trend?.length > 0 
    ? statistics.monthly_trend 
    : emptyStats.monthly_trend

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tahlil</h1>
        <p className="mt-1 text-sm text-gray-500">
          Barcha shartnomalar bo'yicha muvofiqlik muammolari va tahlil natijalari
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-red-500">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">Kritik</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.critical_count}</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-orange-500">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">Yuqori</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.high_count}</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-yellow-500">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">O'rta</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.medium_count}</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-blue-500">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">Ma'lumot</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.info_count}</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-green-500">
              <CheckCircleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">Hal qilingan</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.resolved_count}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Muammolar taqsimoti</h3>
          {(stats.critical_count + stats.high_count + stats.medium_count + stats.low_count + stats.info_count) > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={severityDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {severityDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-4 mt-4 flex-wrap">
                {severityDistribution.map((item) => (
                  <div key={item.name} className="flex items-center text-sm">
                    <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: item.color }} />
                    {item.name}: {item.value}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-[250px] text-gray-400">
              <DocumentMagnifyingGlassIcon className="h-16 w-16 mb-3" />
              <p className="text-sm">Hali muammolar topilmagan</p>
            </div>
          )}
        </div>

        {/* Monthly Trend */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Oylik trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthlyTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="critical" name="Kritik" fill="#EF4444" stackId="a" />
              <Bar dataKey="high" name="Yuqori" fill="#F97316" stackId="a" />
              <Bar dataKey="medium" name="O'rta" fill="#F59E0B" stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Muammo qidirish..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <div className="sm:w-48">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="input-field"
            >
              <option value="">Barcha darajalar</option>
              <option value="critical">Kritik</option>
              <option value="major">Jiddiy</option>
              <option value="minor">Kichik</option>
              <option value="info">Ma'lumot</option>
            </select>
          </div>
          <div className="sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              <option value="">Barcha statuslar</option>
              <option value="open">Ochiq</option>
              <option value="resolved">Hal qilingan</option>
              <option value="ignored">E'tiborsiz</option>
            </select>
          </div>
        </div>
      </div>

      {/* Issues List */}
      <div className="card overflow-hidden">
        {hasIssues ? (
          <ul className="divide-y divide-gray-200">
            {issuesList.map((issue) => (
              <li key={issue.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <ComplianceIssueBadge severity={issue.severity} />
                      {issue.status === 'resolved' && (
                        <span className="badge-success">Hal qilindi</span>
                      )}
                    </div>
                    <h4 className="text-sm font-medium text-gray-900">{issue.title}</h4>
                    <p className="mt-1 text-sm text-gray-600">{issue.description}</p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <Link
                        to={`/contracts/${issue.contract_id}`}
                        className="flex items-center hover:text-primary-600"
                      >
                        <DocumentTextIcon className="h-4 w-4 mr-1" />
                        {issue.contract_title}
                      </Link>
                      <span>{issue.location}</span>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <DocumentMagnifyingGlassIcon className="h-20 w-20 mb-4" />
            <p className="text-lg font-medium text-gray-600 mb-2">Hali muammolar topilmagan</p>
            <p className="text-sm text-gray-500 mb-6">Shartnoma yuklang va tahlil qiling - muammolar shu yerda ko'rsatiladi</p>
            <Link to="/contracts/upload" className="btn-primary">
              Shartnoma yuklash
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
