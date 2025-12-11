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

  // Mock data
  const mockLaws = [
    {
      id: 1,
      name: 'Fuqarolik Kodeksi',
      code: 'FK',
      category: 'civil',
      effective_date: '1996-03-01',
      description: 'O\'zbekiston Respublikasining asosiy fuqarolik qonunchiligi',
      chapters_count: 78,
      articles_count: 1150,
    },
    {
      id: 2,
      name: 'Mehnat Kodeksi',
      code: 'MK',
      category: 'labor',
      effective_date: '1996-04-01',
      description: 'Mehnat munosabatlarini tartibga soluvchi qonun',
      chapters_count: 25,
      articles_count: 450,
    },
    {
      id: 3,
      name: 'Soliq Kodeksi',
      code: 'SK',
      category: 'tax',
      effective_date: '2020-01-01',
      description: 'Soliq tizimi va soliqqa tortish qoidalari',
      chapters_count: 32,
      articles_count: 380,
    },
    {
      id: 4,
      name: 'Xo\'jalik protsessual Kodeksi',
      code: 'XPK',
      category: 'procedural',
      effective_date: '2018-01-01',
      description: 'Iqtisodiy sudlarda ishlarni ko\'rish tartibi',
      chapters_count: 38,
      articles_count: 320,
    },
    {
      id: 5,
      name: 'Ijara to\'g\'risida',
      code: 'IQ',
      category: 'civil',
      effective_date: '1991-11-19',
      description: 'Ijara munosabatlarini tartibga solish',
      chapters_count: 6,
      articles_count: 45,
    },
  ]

  const mockTemplates = [
    {
      id: 1,
      name: 'Xizmat ko\'rsatish shartnomasi',
      contract_type: 'service',
      language: 'uz_latin',
      description: 'Standart xizmat ko\'rsatish shartnomasi namunasi',
      downloads_count: 1245,
    },
    {
      id: 2,
      name: 'Yetkazib berish shartnomasi',
      contract_type: 'supply',
      language: 'uz_latin',
      description: 'Tovarlar yetkazib berish shartnomasi namunasi',
      downloads_count: 987,
    },
    {
      id: 3,
      name: 'Ijara shartnomasi',
      contract_type: 'lease',
      language: 'uz_latin',
      description: 'Ko\'chmas mulk ijara shartnomasi namunasi',
      downloads_count: 756,
    },
    {
      id: 4,
      name: 'Mehnat shartnomasi',
      contract_type: 'employment',
      language: 'uz_latin',
      description: 'Xodim bilan mehnat shartnomasi namunasi',
      downloads_count: 2134,
    },
  ]

  const mockArticles = [
    {
      id: 1,
      article_number: '333',
      title: 'Majburiyatni bajarishdan ozod qiluvchi holatlar',
      content: 'Agar majburiyatni bajarish majburiyat paydo bo\'lganidan keyin yuzaga kelgan fors-major holatlari (favqulodda va oldini olish mumkin bo\'lmagan holatlar) tufayli imkonsiz bo\'lsa, qarzdor majburiyatni bajarish uchun javobgar bo\'lmaydi.',
    },
    {
      id: 2,
      article_number: '260',
      title: 'Neustoyka (jarima, penya)',
      content: 'Neustoyka (jarima, penya) - bu majburiyat bajarilmagan yoki lozim darajada bajarilmagan taqdirda qarzdor kreditorga to\'lashi shart bo\'lgan qonun yoki shartnomada belgilangan pul summasi.',
    },
    {
      id: 3,
      article_number: '354',
      title: 'Shartnomaning shakli',
      content: 'Shartnoma og\'zaki yoki yozma shaklda tuzilishi mumkin. Shartnoma oddiy yozma yoki notarial shaklda tuzilishi mumkin.',
    },
  ]

  const displayLaws = laws?.results || mockLaws
  const displayTemplates = templates?.results || mockTemplates

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
              ) : (
                <ul className="divide-y divide-gray-200">
                  {displayLaws.map((law) => (
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
                  <ul className="divide-y divide-gray-200">
                    {mockArticles.map((article) => (
                      <li key={article.id} className="p-4">
                        <div className="flex items-start">
                          <span className="flex-shrink-0 w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold">
                            {article.article_number}
                          </span>
                          <div className="ml-4">
                            <h4 className="text-sm font-medium text-gray-900">{article.title}</h4>
                            <p className="mt-1 text-sm text-gray-600 line-clamp-3">{article.content}</p>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
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
          ) : (
            displayTemplates.map((template) => (
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
          )}
        </div>
      )}
    </div>
  )
}
