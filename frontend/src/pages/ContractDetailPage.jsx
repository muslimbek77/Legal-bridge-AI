import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeftIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import LoadingSpinner from '../components/LoadingSpinner'
import ContractStatusBadge from '../components/ContractStatusBadge'
import { RiskScoreCircle } from '../components/RiskScoreBadge'
import ComplianceIssueBadge from '../components/ComplianceIssueBadge'
import contractsService from '../services/contracts'
import analysisService from '../services/analysis'
import reportsService from '../services/reports'

export default function ContractDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: contract, isLoading: contractLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractsService.getContract(id),
  })

  const { data: analysisData } = useQuery({
    queryKey: ['contract-analysis', id],
    queryFn: () => analysisService.getAnalysisByContract(id),
    enabled: !!contract && contract.status === 'analyzed',
  })

  // Mock data for demo
  const mockContract = {
    id: 1,
    title: 'IT xizmatlari shartnomasi',
    contract_type: 'service',
    status: 'analyzed',
    language: 'uz_latin',
    counterparty_name: 'TechSolutions LLC',
    counterparty_inn: '123456789',
    contract_number: '2024/001',
    description: 'Dasturiy ta\'minot ishlab chiqish va texnik qo\'llab-quvvatlash xizmatlari',
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T11:45:00Z',
    file: '/media/contracts/contract_001.pdf',
    extracted_text: 'Shartnoma matni...',
  }

  const mockAnalysis = {
    id: 1,
    risk_score: 35,
    compliance_score: 87,
    summary: 'Shartnoma umumiy jihatdan O\'zbekiston qonunchiligiga mos keladi. Bir nechta kichik muammolar aniqlandi.',
    processing_time: 45.2,
    created_at: '2024-01-15T11:45:00Z',
    issues: [
      {
        id: 1,
        severity: 'minor',
        title: 'Force majeure bandida etishmovchilik',
        description: 'Fors-major holatlari ro\'yxatida tabiiy ofatlar to\'liq ko\'rsatilmagan',
        location: 'Band 8.1',
        recommendation: 'Fuqarolik Kodeksining 333-moddasiga muvofiq force majeure holatlarini to\'ldiring',
        law_reference: 'Fuqarolik Kodeksi, 333-modda',
        status: 'open',
      },
      {
        id: 2,
        severity: 'info',
        title: 'Nizolarni hal qilish tartibi',
        description: 'Hakamlik sudi orqali nizolarni hal qilish imkoniyati ko\'rsatilmagan',
        location: 'Band 9.2',
        recommendation: 'Hakamlik sudi to\'g\'risidagi bandni qo\'shish tavsiya etiladi',
        law_reference: 'Hakamlik sudlari to\'g\'risidagi qonun',
        status: 'open',
      },
      {
        id: 3,
        severity: 'major',
        title: 'Jarima va peniya miqdori',
        description: 'Belgilangan jarima miqdori qonuniy chegaradan oshgan',
        location: 'Band 7.3',
        recommendation: 'Jarima miqdorini 50% dan oshmaydigan qilib o\'zgartiring',
        law_reference: 'Fuqarolik Kodeksi, 260-modda',
        status: 'resolved',
      },
    ],
    key_terms: [
      { term: 'Shartnoma muddati', value: '12 oy', location: 'Band 2.1' },
      { term: 'Shartnoma summasi', value: '150,000,000 so\'m', location: 'Band 3.1' },
      { term: 'To\'lov muddati', value: '30 kun', location: 'Band 3.3' },
      { term: 'Kafolat muddati', value: '6 oy', location: 'Band 5.2' },
    ],
    sections: [
      { title: 'Umumiy qoidalar', risk: 'low', issues_count: 0 },
      { title: 'Shartnoma predmeti', risk: 'low', issues_count: 0 },
      { title: 'To\'lov shartlari', risk: 'low', issues_count: 0 },
      { title: 'Tomonlarning majburiyatlari', risk: 'medium', issues_count: 1 },
      { title: 'Javobgarlik', risk: 'high', issues_count: 1 },
      { title: 'Force majeure', risk: 'medium', issues_count: 1 },
      { title: 'Nizolarni hal qilish', risk: 'low', issues_count: 0 },
    ],
  }

  const displayContract = contract || mockContract
  const displayAnalysis = analysisData?.results?.[0] || mockAnalysis

  const analyzeMutation = useMutation({
    mutationFn: () => contractsService.analyzeContract(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['contract', id])
      queryClient.invalidateQueries(['contract-analysis', id])
      toast.success('Tahlil boshlandi')
    },
    onError: () => {
      toast.error('Tahlil boshlashda xatolik')
    },
  })

  const generateReportMutation = useMutation({
    mutationFn: (format) => reportsService.generateReport(id, format),
    onSuccess: () => {
      toast.success('Hisobot yaratildi')
      queryClient.invalidateQueries(['reports'])
    },
    onError: () => {
      toast.error('Hisobot yaratishda xatolik')
    },
  })

  if (contractLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'high': return 'text-orange-600 bg-orange-50'
      case 'critical': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Orqaga
          </button>
          <div className="flex items-center gap-4">
            <DocumentTextIcon className="h-10 w-10 text-gray-400" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{displayContract.title}</h1>
              <div className="mt-1 flex items-center gap-3">
                <ContractStatusBadge status={displayContract.status} />
                <span className="text-sm text-gray-500">
                  {format(new Date(displayContract.created_at), 'dd.MM.yyyy HH:mm')}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {displayContract.status !== 'analyzed' && (
            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="btn-primary"
            >
              <ArrowPathIcon className={`h-5 w-5 mr-2 ${analyzeMutation.isPending ? 'animate-spin' : ''}`} />
              Tahlil qilish
            </button>
          )}
          <div className="relative group">
            <button className="btn-secondary">
              <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
              Hisobot
            </button>
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 hidden group-hover:block z-10">
              <div className="py-1">
                <button
                  onClick={() => generateReportMutation.mutate('pdf')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  PDF formatda
                </button>
                <button
                  onClick={() => generateReportMutation.mutate('docx')}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  DOCX formatda
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Contract Info & Analysis */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contract Info */}
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Shartnoma ma'lumotlari</h3>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Shartnoma raqami</dt>
                <dd className="mt-1 text-sm text-gray-900">{displayContract.contract_number || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Shartnoma turi</dt>
                <dd className="mt-1 text-sm text-gray-900">{displayContract.contract_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Kontragent</dt>
                <dd className="mt-1 text-sm text-gray-900">{displayContract.counterparty_name || '-'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">INN</dt>
                <dd className="mt-1 text-sm text-gray-900">{displayContract.counterparty_inn || '-'}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-sm font-medium text-gray-500">Izoh</dt>
                <dd className="mt-1 text-sm text-gray-900">{displayContract.description || '-'}</dd>
              </div>
            </dl>
          </div>

          {/* Analysis Summary */}
          {displayContract.status === 'analyzed' && displayAnalysis && (
            <>
              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Tahlil xulosasi</h3>
                <p className="text-sm text-gray-600">{displayAnalysis.summary}</p>
                <div className="mt-4 flex items-center text-xs text-gray-500">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  Tahlil vaqti: {displayAnalysis.processing_time?.toFixed(1)} soniya
                </div>
              </div>

              {/* Key Terms */}
              <div className="card p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Asosiy shartlar</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Shart</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Qiymat</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Joylashuv</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {displayAnalysis.key_terms?.map((term, index) => (
                        <tr key={index}>
                          <td className="px-4 py-3 text-sm text-gray-900">{term.term}</td>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{term.value}</td>
                          <td className="px-4 py-3 text-sm text-gray-500">{term.location}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Compliance Issues */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-medium text-gray-900">Muvofiqlik muammolari</h3>
                </div>
                <ul className="divide-y divide-gray-200">
                  {displayAnalysis.issues?.map((issue) => (
                    <li key={issue.id} className="p-4">
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
                          <p className="mt-2 text-xs text-gray-500">
                            <span className="font-medium">Joylashuv:</span> {issue.location}
                          </p>
                          <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                            <p className="text-sm text-blue-800">
                              <span className="font-medium">Tavsiya:</span> {issue.recommendation}
                            </p>
                            <p className="mt-1 text-xs text-blue-600">
                              <span className="font-medium">Qonun:</span> {issue.law_reference}
                            </p>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}

          {/* Processing status */}
          {displayContract.status === 'processing' && (
            <div className="card p-8 text-center">
              <LoadingSpinner size="lg" className="mb-4" />
              <h3 className="text-lg font-medium text-gray-900">Tahlil qilinmoqda...</h3>
              <p className="mt-2 text-sm text-gray-500">
                Shartnoma sun'iy intellekt yordamida tahlil qilinmoqda. Bu 1-2 daqiqa davom etishi mumkin.
              </p>
            </div>
          )}
        </div>

        {/* Right Column - Risk Score & Sections */}
        <div className="space-y-6">
          {/* Risk Score */}
          {displayContract.status === 'analyzed' && displayAnalysis && (
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 text-center">Risk Bahosi</h3>
              <div className="flex justify-center mb-4">
                <RiskScoreCircle score={displayAnalysis.risk_score} size={160} />
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Muvofiqlik</span>
                  <span className="text-sm font-semibold text-green-600">{displayAnalysis.compliance_score}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${displayAnalysis.compliance_score}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Issue Summary */}
          {displayContract.status === 'analyzed' && displayAnalysis?.issues && (
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Muammolar xulosasi</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
                    <span className="text-sm text-gray-600">Kritik</span>
                  </div>
                  <span className="font-semibold text-red-600">
                    {displayAnalysis.issues.filter(i => i.severity === 'critical').length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-orange-500 mr-2" />
                    <span className="text-sm text-gray-600">Jiddiy</span>
                  </div>
                  <span className="font-semibold text-orange-600">
                    {displayAnalysis.issues.filter(i => i.severity === 'major').length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2" />
                    <span className="text-sm text-gray-600">Kichik</span>
                  </div>
                  <span className="font-semibold text-yellow-600">
                    {displayAnalysis.issues.filter(i => i.severity === 'minor').length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <InformationCircleIcon className="h-5 w-5 text-blue-500 mr-2" />
                    <span className="text-sm text-gray-600">Ma'lumot</span>
                  </div>
                  <span className="font-semibold text-blue-600">
                    {displayAnalysis.issues.filter(i => i.severity === 'info').length}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Sections Analysis */}
          {displayContract.status === 'analyzed' && displayAnalysis?.sections && (
            <div className="card p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Bo'limlar tahlili</h3>
              <ul className="space-y-2">
                {displayAnalysis.sections.map((section, index) => (
                  <li key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <span className="text-sm text-gray-700">{section.title}</span>
                    <div className="flex items-center gap-2">
                      {section.issues_count > 0 && (
                        <span className="text-xs text-gray-500">{section.issues_count}</span>
                      )}
                      <span className={`px-2 py-0.5 text-xs rounded ${getRiskColor(section.risk)}`}>
                        {section.risk === 'low' ? 'Past' : section.risk === 'medium' ? 'O\'rta' : section.risk === 'high' ? 'Yuqori' : 'Kritik'}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
