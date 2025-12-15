import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
  MagnifyingGlassIcon,
  BookOpenIcon,
  DocumentTextIcon,
  ChevronRightIcon,
  ArrowDownTrayIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  EyeIcon,
  XMarkIcon,
  PrinterIcon,
  LanguageIcon,
} from '@heroicons/react/24/outline'
import LoadingSpinner from '../components/LoadingSpinner'
import legalDatabaseService from '../services/legalDatabase'

export default function LegalDatabasePage() {
  const [activeTab, setActiveTab] = useState('laws')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedLaw, setSelectedLaw] = useState(null)
  const [expandedArticle, setExpandedArticle] = useState(null)
  const [previewTemplate, setPreviewTemplate] = useState(null)
  const [downloadLang, setDownloadLang] = useState('uz_latin')
  const [showLangMenu, setShowLangMenu] = useState(null)
  const [previewLang, setPreviewLang] = useState('uz_latin')

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

  // Tanlangan qonunning moddalarini olish
  const { data: lawDetail, isLoading: lawDetailLoading } = useQuery({
    queryKey: ['law-detail', selectedLaw?.id],
    queryFn: () => legalDatabaseService.getLaw(selectedLaw.id),
    enabled: !!selectedLaw?.id,
  })

  // Haqiqiy ma'lumotlarni ishlatish
  const lawsList = laws?.results || []
  const templatesList = templates?.results || []
  const hasLaws = lawsList.length > 0
  const hasTemplates = templatesList.length > 0
  const articles = lawDetail?.articles || []

  const handleDownloadTemplate = async (template, lang = 'uz_latin') => {
    try {
      const blob = await legalDatabaseService.downloadTemplate(template.id, lang)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const langSuffix = { uz_latin: 'lotin', uz_cyrillic: 'kirill', ru: 'rus' }
      a.download = `${template.name}_${langSuffix[lang] || 'lotin'}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      setShowLangMenu(null)
      toast.success('Shablon PDF formatda yuklab olindi')
    } catch (error) {
      console.error('Download error:', error)
      toast.error('Yuklab olishda xatolik yuz berdi')
    }
  }

  const langOptions = [
    { value: 'uz_latin', label: "O'zbek (lotin)", flag: '🇺🇿' },
    { value: 'uz_cyrillic', label: "O'zbek (kirill)", flag: '🇺🇿' },
    { value: 'ru', label: 'Русский', flag: '🇷🇺' },
  ]

  const handlePrint = () => {
    window.print()
  }

  const contractTypeLabels = {
    employment: 'Mehnat shartnomasi',
    lease: 'Ijara shartnomasi',
    sale: 'Oldi-sotdi shartnomasi',
    service: 'Xizmat ko\'rsatish',
    contract: 'Pudrat shartnomasi',
    supply: 'Yetkazib berish',
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
                      <div className="mt-2 flex items-center gap-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                          {selectedLaw.short_name}
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {selectedLaw.law_type_display}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          selectedLaw.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {selectedLaw.status_display}
                        </span>
                      </div>
                    </div>
                  </div>
                  <dl className="grid grid-cols-3 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <dt className="text-xs text-gray-500">Raqami</dt>
                      <dd className="text-sm font-semibold text-gray-900">{selectedLaw.number || '-'}</dd>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <dt className="text-xs text-gray-500">Moddalar</dt>
                      <dd className="text-lg font-semibold text-gray-900">{selectedLaw.articles_count}</dd>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 text-center">
                      <dt className="text-xs text-gray-500">Qabul qilingan</dt>
                      <dd className="text-sm font-semibold text-gray-900">{selectedLaw.adoption_date || '-'}</dd>
                    </div>
                  </dl>
                </div>

                {/* Articles List */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="text-lg font-medium text-gray-900">Moddalar ({articles.length})</h3>
                  </div>
                  {lawDetailLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <LoadingSpinner />
                    </div>
                  ) : articles.length > 0 ? (
                    <div className="divide-y divide-gray-200">
                      {articles.map((article) => (
                        <div key={article.id} className="p-4">
                          <button
                            onClick={() => setExpandedArticle(expandedArticle === article.id ? null : article.id)}
                            className="w-full flex items-center justify-between text-left"
                          >
                            <div>
                              <span className="text-sm font-medium text-primary-600">{article.number}-modda.</span>
                              <span className="ml-2 text-sm font-medium text-gray-900">{article.title}</span>
                            </div>
                            {expandedArticle === article.id ? (
                              <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                            ) : (
                              <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                            )}
                          </button>
                          {expandedArticle === article.id && (
                            <div className="mt-3 pl-4 border-l-2 border-primary-200">
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">{article.content}</p>
                              {article.is_mandatory && (
                                <span className="mt-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                                  Majburiy
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center text-gray-500">
                      <BookOpenIcon className="h-10 w-10 mx-auto mb-3 text-gray-400" />
                      <p className="text-sm">Bu qonun uchun moddalar hali qo'shilmagan</p>
                    </div>
                  )}
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
              <div key={template.id} className="card hover:shadow-lg transition-shadow overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-primary-500 to-primary-600 px-6 py-4">
                  <div className="flex items-center justify-between">
                    <DocumentTextIcon className="h-8 w-8 text-white" />
                    <span className="text-xs text-primary-100 bg-primary-700 px-2 py-1 rounded">
                      {contractTypeLabels[template.contract_type] || template.contract_type}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-white mt-3">{template.name}</h3>
                </div>
                
                {/* Body */}
                <div className="p-6">
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{template.description}</p>
                  
                  {/* Related Laws */}
                  {template.related_laws && template.related_laws.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs text-gray-500 mb-2">Tegishli qonunlar:</p>
                      <div className="flex flex-wrap gap-1">
                        {template.related_laws.slice(0, 3).map(law => (
                          <span key={law.id} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
                            {law.short_name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Required Sections */}
                  {template.required_sections && template.required_sections.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs text-gray-500 mb-2">Majburiy bo'limlar: {template.required_sections.length} ta</p>
                    </div>
                  )}
                  
                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-4 border-t border-gray-100">
                    <button
                      onClick={() => setPreviewTemplate(template)}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
                    >
                      <EyeIcon className="h-4 w-4 mr-1" />
                      Ko'rish
                    </button>
                    <div className="relative flex-1">
                      <button
                        onClick={() => setShowLangMenu(showLangMenu === template.id ? null : template.id)}
                        className="w-full inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                      >
                        <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                        PDF
                        <ChevronDownIcon className="h-3 w-3 ml-1" />
                      </button>
                      {showLangMenu === template.id && (
                        <div className="absolute bottom-full left-0 right-0 mb-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                          {langOptions.map((lang) => (
                            <button
                              key={lang.value}
                              onClick={() => handleDownloadTemplate(template, lang.value)}
                              className="w-full px-3 py-2 text-sm text-left hover:bg-gray-50 flex items-center gap-2"
                            >
                              <span>{lang.flag}</span>
                              <span>{lang.label}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
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

      {/* Template Preview Modal */}
      {previewTemplate && (
        <div className="fixed inset-0 z-50 overflow-y-auto print:relative print:overflow-visible">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
            {/* Backdrop */}
            <div 
              className="fixed inset-0 bg-gray-900 bg-opacity-75 transition-opacity print:hidden"
              onClick={() => setPreviewTemplate(null)}
            />
            
            {/* Modal */}
            <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full mx-auto my-8 print:shadow-none print:rounded-none print:max-w-none print:m-0">
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 print:hidden">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    {previewLang === 'ru' ? previewTemplate.name_ru || previewTemplate.name : 
                     previewLang === 'uz_cyrillic' ? previewTemplate.name_cyrillic || previewTemplate.name : 
                     previewTemplate.name}
                  </h2>
                  {/* Language Switcher */}
                  <div className="flex items-center gap-1 mt-2">
                    {langOptions.map((lang) => (
                      <button
                        key={lang.value}
                        onClick={() => setPreviewLang(lang.value)}
                        className={`px-2 py-1 text-xs rounded ${
                          previewLang === lang.value 
                            ? 'bg-primary-600 text-white' 
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {lang.flag} {lang.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrint}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                  >
                    <PrinterIcon className="h-4 w-4 mr-1" />
                    Chop etish
                  </button>
                  <div className="relative">
                    <button
                      onClick={() => setShowLangMenu(showLangMenu === 'modal' ? null : 'modal')}
                      className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
                    >
                      <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                      PDF yuklash
                      <ChevronDownIcon className="h-3 w-3 ml-1" />
                    </button>
                    {showLangMenu === 'modal' && (
                      <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20 min-w-[160px]">
                        {langOptions.map((lang) => (
                          <button
                            key={lang.value}
                            onClick={() => handleDownloadTemplate(previewTemplate, lang.value)}
                            className="w-full px-3 py-2 text-sm text-left hover:bg-gray-50 flex items-center gap-2"
                          >
                            <span>{lang.flag}</span>
                            <span>{lang.label}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setPreviewTemplate(null)}
                    className="p-2 text-gray-400 hover:text-gray-500"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>
              </div>
              
              {/* Contract Document View */}
              <div className="p-8 bg-gray-50 print:bg-white print:p-0">
                <div className="bg-white shadow-lg mx-auto max-w-3xl print:shadow-none print:max-w-none">
                  {/* A4 Paper Style */}
                  <div className="p-12 min-h-[800px] font-serif text-gray-800 leading-relaxed print:p-8">
                    {/* Document Content */}
                    <div className="whitespace-pre-wrap text-sm">
                      {(() => {
                        const text = previewLang === 'ru' ? (previewTemplate.template_text_ru || previewTemplate.template_text) :
                                     previewLang === 'uz_cyrillic' ? (previewTemplate.template_text_cyrillic || previewTemplate.template_text) :
                                     previewTemplate.template_text;
                        return text?.split('\n').map((line, index) => {
                        // Title lines (all caps or with №)
                        if (line.match(/^[A-ZА-ЯЁ\s]{10,}/) || line.includes('№') || line.match(/^[0-9]+\.\s+[A-ZА-ЯЁ]/)) {
                          return (
                            <p key={index} className="text-center font-bold text-base mb-4 mt-6">
                              {line}
                            </p>
                          )
                        }
                        // Section headers (numbered)
                        if (line.match(/^[0-9]+\.\s+[A-ZА-ЯЁa-zа-яё]/i)) {
                          return (
                            <p key={index} className="font-bold text-base mt-6 mb-2">
                              {line}
                            </p>
                          )
                        }
                        // Subsection items
                        if (line.match(/^[0-9]+\.[0-9]+\./)) {
                          return (
                            <p key={index} className="pl-4 mb-1">
                              {line}
                            </p>
                          )
                        }
                        // Signature lines
                        if (line.includes('_____') || line.includes('M.O.') || line.includes('М.П.')) {
                          return (
                            <p key={index} className="mt-2">
                              {line}
                            </p>
                          )
                        }
                        // Empty lines
                        if (line.trim() === '') {
                          return <br key={index} />
                        }
                        // Regular text
                        return (
                          <p key={index} className="mb-1">
                            {line}
                          </p>
                        )
                      });
                      })()}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Related Laws Section */}
              {previewTemplate.related_laws && previewTemplate.related_laws.length > 0 && (
                <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 print:hidden">
                  <p className="text-sm font-medium text-gray-700 mb-2">Tegishli qonunchilik asoslari:</p>
                  <div className="flex flex-wrap gap-2">
                    {previewTemplate.related_laws.map(law => (
                      <span key={law.id} className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                        {law.short_name}: {law.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
