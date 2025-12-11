import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  DocumentTextIcon,
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

  const { data: issues, isLoading } = useQuery({
    queryKey: ['compliance-issues', severityFilter, statusFilter, searchTerm],
    queryFn: () => analysisService.getComplianceIssues({
      severity: severityFilter,
      status: statusFilter,
      search: searchTerm,
    }),
  })

  // Mock data
  const mockIssues = [
    {
      id: 1,
      severity: 'critical',
      title: 'Majburiy shartlarning etishmasligi',
      description: 'Shartnomada qonun talabiga ko\'ra bo\'lishi shart bo\'lgan band mavjud emas',
      contract_title: 'IT xizmatlari shartnomasi',
      contract_id: 1,
      location: 'Band 3.2',
      status: 'open',
      created_at: '2024-01-15T10:30:00Z',
    },
    {
      id: 2,
      severity: 'major',
      title: 'Jarima miqdori chegaradan oshgan',
      description: 'Belgilangan jarima qonuniy maksimal miqdordan yuqori',
      contract_title: 'Yetkazib berish shartnomasi',
      contract_id: 2,
      location: 'Band 7.3',
      status: 'open',
      created_at: '2024-01-14T14:20:00Z',
    },
    {
      id: 3,
      severity: 'minor',
      title: 'Force majeure bandida etishmovchilik',
      description: 'Fors-major holatlari ro\'yxati to\'liq emas',
      contract_title: 'Ijara shartnomasi',
      contract_id: 3,
      location: 'Band 8.1',
      status: 'resolved',
      created_at: '2024-01-13T09:15:00Z',
    },
    {
      id: 4,
      severity: 'info',
      title: 'Hakamlik sudi to\'g\'risida band yo\'q',
      description: 'Nizolarni hakamlik sudi orqali hal qilish imkoniyati ko\'rsatilmagan',
      contract_title: 'Konsalting shartnomasi',
      contract_id: 4,
      location: 'Band 9',
      status: 'open',
      created_at: '2024-01-12T16:45:00Z',
    },
  ]

  const mockStats = {
    total_issues: 156,
    critical_count: 12,
    major_count: 34,
    minor_count: 67,
    info_count: 43,
    resolved_count: 89,
    open_count: 67,
    severity_distribution: [
      { name: 'Kritik', value: 12, color: '#EF4444' },
      { name: 'Jiddiy', value: 34, color: '#F97316' },
      { name: 'Kichik', value: 67, color: '#F59E0B' },
      { name: 'Ma\'lumot', value: 43, color: '#3B82F6' },
    ],
    monthly_trend: [
      { month: 'Yan', critical: 2, major: 5, minor: 10 },
      { month: 'Fev', critical: 3, major: 8, minor: 15 },
      { month: 'Mar', critical: 1, major: 4, minor: 12 },
      { month: 'Apr', critical: 4, major: 6, minor: 8 },
      { month: 'May', critical: 2, major: 7, minor: 14 },
      { month: 'Iyun', critical: 0, major: 4, minor: 8 },
    ],
  }

  const displayIssues = issues?.results || mockIssues

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
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-red-500">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">Kritik</p>
              <p className="text-2xl font-semibold text-gray-900">{mockStats.critical_count}</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-orange-500">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">Jiddiy</p>
              <p className="text-2xl font-semibold text-gray-900">{mockStats.major_count}</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0 rounded-md p-3 bg-yellow-500">
              <ExclamationTriangleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-500">Kichik</p>
              <p className="text-2xl font-semibold text-gray-900">{mockStats.minor_count}</p>
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
              <p className="text-2xl font-semibold text-gray-900">{mockStats.resolved_count}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Muammolar taqsimoti</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={mockStats.severity_distribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {mockStats.severity_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-4">
            {mockStats.severity_distribution.map((item) => (
              <div key={item.name} className="flex items-center text-sm">
                <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: item.color }} />
                {item.name}: {item.value}
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Trend */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Oylik trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={mockStats.monthly_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="critical" name="Kritik" fill="#EF4444" stackId="a" />
              <Bar dataKey="major" name="Jiddiy" fill="#F97316" stackId="a" />
              <Bar dataKey="minor" name="Kichik" fill="#F59E0B" stackId="a" />
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
        <ul className="divide-y divide-gray-200">
          {displayIssues.map((issue) => (
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
      </div>
    </div>
  )
}
