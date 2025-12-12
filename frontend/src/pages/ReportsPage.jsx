import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DocumentArrowDownIcon,
  TrashIcon,
  EnvelopeIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import reportsService from '../services/reports'

export default function ReportsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [formatFilter, setFormatFilter] = useState('')
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [emailModalOpen, setEmailModalOpen] = useState(false)
  const [selectedReport, setSelectedReport] = useState(null)
  const [emailAddress, setEmailAddress] = useState('')

  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['reports', searchTerm, formatFilter],
    queryFn: () => reportsService.getReports({
      search: searchTerm,
      format: formatFilter,
    }),
  })

  const deleteMutation = useMutation({
    mutationFn: reportsService.deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries(['reports'])
      toast.success('Hisobot o\'chirildi')
      setDeleteModalOpen(false)
    },
    onError: () => {
      toast.error('Xatolik yuz berdi')
    },
  })

  const sendEmailMutation = useMutation({
    mutationFn: ({ id, email }) => reportsService.sendByEmail(id, email),
    onSuccess: () => {
      toast.success('Hisobot yuborildi')
      setEmailModalOpen(false)
      setEmailAddress('')
    },
    onError: () => {
      toast.error('Yuborishda xatolik')
    },
  })

  // Haqiqiy ma'lumotlarni ishlatish
  const reportsList = data?.results || []
  const hasReports = reportsList.length > 0

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleDownload = async (report) => {
    try {
      const blob = await reportsService.downloadReport(report.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${report.contract_title}.${report.format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      toast.success('Hisobot yuklab olindi')
    } catch {
      toast.error('Yuklab olishda xatolik')
    }
  }

  const handleDelete = (report) => {
    setSelectedReport(report)
    setDeleteModalOpen(true)
  }

  const handleEmail = (report) => {
    setSelectedReport(report)
    setEmailModalOpen(true)
  }

  const confirmDelete = () => {
    if (selectedReport) {
      deleteMutation.mutate(selectedReport.id)
    }
  }

  const confirmSendEmail = () => {
    if (selectedReport && emailAddress) {
      sendEmailMutation.mutate({ id: selectedReport.id, email: emailAddress })
    }
  }

  const getRiskScoreClass = (score) => {
    if (score < 25) return 'bg-green-100 text-green-800'
    if (score < 50) return 'bg-yellow-100 text-yellow-800'
    if (score < 75) return 'bg-orange-100 text-orange-800'
    return 'bg-red-100 text-red-800'
  }

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
        <h1 className="text-2xl font-bold text-gray-900">Hisobotlar</h1>
        <p className="mt-1 text-sm text-gray-500">
          Yaratilgan tahlil hisobotlari
        </p>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Hisobot qidirish..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <div className="sm:w-48">
            <select
              value={formatFilter}
              onChange={(e) => setFormatFilter(e.target.value)}
              className="input-field"
            >
              <option value="">Barcha formatlar</option>
              <option value="pdf">PDF</option>
              <option value="docx">DOCX</option>
              <option value="html">HTML</option>
            </select>
          </div>
        </div>
      </div>

      {/* Reports Table */}
      <div className="card overflow-hidden">
        {!hasReports ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <DocumentArrowDownIcon className="h-12 w-12 mb-4" />
            <p className="text-lg font-medium">Hisobotlar topilmadi</p>
            <p className="text-sm">Shartnomalarni tahlil qilib hisobot yarating</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Shartnoma
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Format
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Ball
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Hajmi
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sana
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amallar
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reportsList.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {report.contract_title}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800 uppercase">
                        {report.format}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskScoreClass(report.risk_score)}`}>
                        {report.risk_score}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatFileSize(report.file_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(report.created_at), 'dd.MM.yyyy HH:mm')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleDownload(report)}
                          className="text-primary-600 hover:text-primary-900"
                          title="Yuklab olish"
                        >
                          <DocumentArrowDownIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleEmail(report)}
                          className="text-green-600 hover:text-green-900"
                          title="Email orqali yuborish"
                        >
                          <EnvelopeIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(report)}
                          className="text-red-600 hover:text-red-900"
                          title="O'chirish"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Hisobotni o'chirish"
      >
        <p className="text-sm text-gray-500">
          Haqiqatan ham bu hisobotni o'chirmoqchimisiz?
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setDeleteModalOpen(false)}
          >
            Bekor qilish
          </button>
          <button
            type="button"
            className="btn-danger"
            onClick={confirmDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'O\'chirilmoqda...' : 'O\'chirish'}
          </button>
        </div>
      </Modal>

      {/* Email Modal */}
      <Modal
        isOpen={emailModalOpen}
        onClose={() => setEmailModalOpen(false)}
        title="Hisobotni yuborish"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            Hisobotni qaysi email manziliga yubormoqchisiz?
          </p>
          <input
            type="email"
            value={emailAddress}
            onChange={(e) => setEmailAddress(e.target.value)}
            placeholder="email@example.com"
            className="input-field"
          />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setEmailModalOpen(false)}
          >
            Bekor qilish
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={confirmSendEmail}
            disabled={sendEmailMutation.isPending || !emailAddress}
          >
            {sendEmailMutation.isPending ? 'Yuborilmoqda...' : 'Yuborish'}
          </button>
        </div>
      </Modal>
    </div>
  )
}
