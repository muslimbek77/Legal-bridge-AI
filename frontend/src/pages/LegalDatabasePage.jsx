import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  MagnifyingGlassIcon,
  BookOpenIcon,
  DocumentTextIcon,
  ChevronRightIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline'
import LoadingSpinner from '../components/LoadingSpinner'
import legalDatabaseService from '../services/legalDatabase'

export default function LegalDatabasePage() {
  const [activeTab, setActiveTab] = useState('laws')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedLaw, setSelectedLaw] = useState(null)

  const { data: laws, isLoading: lawsLoading } = useQuery({
    queryKey: ['laws', searchTerm],
    queryFn: () => legalDatabaseService.getLaws({ search: searchTerm }),
    enabled: activeTab === 'laws',
  })

  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ['templates', searchTerm],
    queryFn: () => legalDatabaseService.getTemplates({ search: searchTerm }),
    enabled: activeTab === 'templates',
  })

  // Haqiqiy ma'lumotlarni ishlatish
  const lawsList = laws?.results || []
  const templatesList = templates?.results || []
  const hasLaws = lawsList.length > 0
  const hasTemplates = templatesList.length > 0

  const handleDownloadTemplate = async (template) => {
    try {
      const blob = await legalDatabaseService.downloadTemplate(template.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${template.name}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download error:', error)
    }
  }

  const categoryLabels = {
    civil: 'Fuqarolik',
    labor: 'Mehnat',
    tax: 'Soliq',
    procedural: 'Protsessual',
    administrative: 'Ma\'muriy',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Qonunlar bazasi</h1>
        <p className="mt-1 text-sm text-gray-500">
          O'zbekiston qonunchiligi va shartnoma namunalari
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('laws')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'laws'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <BookOpenIcon className="h-5 w-5 inline mr-2" />
            Qonunlar
          </button>
          <button
            onClick={() => setActiveTab('templates')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'templates'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <DocumentTextIcon className="h-5 w-5 inline mr-2" />
            Shartnoma namunalari
          </button>
        </nav>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder={activeTab === 'laws' ? 'Qonun qidirish...' : 'Namuna qidirish...'}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input-field pl-10"
        />
      </div>

      {/* Content */}
      {activeTab === 'laws' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Laws List */}
          <div className="lg:col-span-1">
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-medium text-gray-900">Qonunlar ro'yxati</h3>
              </div>
              {lawsLoading ? (
                <div className="flex items-center justify-center h-64">
                  <LoadingSpinner />
                </div>
              ) : hasLaws ? (
                <ul className="divide-y divide-gray-200">
                  {lawsList.map((law) => (
                    <li key={law.id}>
                      <button
                        onClick={() => setSelectedLaw(law)}
                        className={`w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between ${
                          selectedLaw?.id === law.id ? 'bg-primary-50' : ''
                        }`}
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-900">{law.name}</p>
                          <p className="text-xs text-gray-500">{law.code}</p>
                        </div>
                        <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                  <BookOpenIcon className="h-12 w-12 mb-3" />
                  <p className="text-sm">Qonunlar bazasi bo'sh</p>
                </div>
              )}
            </div>
          </div>

          {/* Law Details */}
          <div className="lg:col-span-2">
            {selectedLaw ? (
              <div className="space-y-6">
                <div className="card p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">{selectedLaw.name}</h2>
                      <span className="mt-1 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                        {selectedLaw.code}
                      </span>
                    </div>
                    <span className="text-sm text-gray-500">
                      {categoryLabels[selectedLaw.category]}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-4">{selectedLaw.description}</p>
                  <dl className="grid grid-cols-3 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <dt className="text-xs text-gray-500">Boblar</dt>
                      <dd className="text-lg font-semibold text-gray-900">{selectedLaw.chapters_count}</dd>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <dt className="text-xs text-gray-500">Moddalar</dt>
                      <dd className="text-lg font-semibold text-gray-900">{selectedLaw.articles_count}</dd>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <dt className="text-xs text-gray-500">Kuchga kirgan</dt>
                      <dd className="text-sm font-semibold text-gray-900">{selectedLaw.effective_date}</dd>
                    </div>
                  </dl>
                </div>

                {/* Sample Articles */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="text-lg font-medium text-gray-900">Ko'p ishlatiladigan moddalar</h3>
                  </div>
                  <div className="p-6 text-center text-gray-500">
                    <BookOpenIcon className="h-10 w-10 mx-auto mb-3 text-gray-400" />
                    <p className="text-sm">Moddalar tez orada qo'shiladi</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="card p-8 text-center text-gray-500">
                <BookOpenIcon className="h-12 w-12 mx-auto mb-4" />
                <p>Qonun tanlang</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templatesLoading ? (
            <div className="col-span-full flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : hasTemplates ? (
            templatesList.map((template) => (
              <div key={template.id} className="card p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <DocumentTextIcon className="h-10 w-10 text-primary-500" />
                  <span className="text-xs text-gray-500">
                    {template.downloads_count} yuklab olish
                  </span>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">{template.name}</h3>
                <p className="text-sm text-gray-500 mb-4">{template.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
                    {template.language === 'uz_latin' ? 'O\'zbek (lotin)' : 
                     template.language === 'uz_cyrillic' ? 'Ўзбек (кирилл)' : 'Русский'}
                  </span>
                  <button
                    onClick={() => handleDownloadTemplate(template)}
                    className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                    Yuklab olish
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full flex flex-col items-center justify-center py-16 text-gray-400">
              <DocumentTextIcon className="h-16 w-16 mb-4" />
              <p className="text-lg font-medium text-gray-600">Shartnoma namunalari yo'q</p>
              <p className="text-sm text-gray-500">Namunalar tez orada qo'shiladi</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
