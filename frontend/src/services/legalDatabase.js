import api from './api'

export const legalDatabaseService = {
  // Get all laws
  getLaws: async (params = {}) => {
    const response = await api.get('/api/v1/legal/laws/', { params })
    return response.data
  },
  
  // Get single law
  getLaw: async (id) => {
    const response = await api.get(`/api/v1/legal/laws/${id}/`)
    return response.data
  },
  
  // Search laws
  searchLaws: async (query) => {
    const response = await api.get('/api/v1/legal/laws/', {
      params: { search: query }
    })
    return response.data
  },
  
  // Get law chapters
  getChapters: async (lawId) => {
    const response = await api.get('/api/v1/legal/chapters/', {
      params: { law: lawId }
    })
    return response.data
  },
  
  // Get law articles
  getArticles: async (params = {}) => {
    const response = await api.get('/api/v1/legal/articles/', { params })
    return response.data
  },
  
  // Get single article
  getArticle: async (id) => {
    const response = await api.get(`/api/v1/legal/articles/${id}/`)
    return response.data
  },
  
  // Get legal rules
  getRules: async (params = {}) => {
    const response = await api.get('/api/v1/legal/rules/', { params })
    return response.data
  },
  
  // Get contract templates
  getTemplates: async (params = {}) => {
    const response = await api.get('/api/v1/legal/templates/', { params })
    return response.data
  },
  
  // Get single template
  getTemplate: async (id) => {
    const response = await api.get(`/api/v1/legal/templates/${id}/`)
    return response.data
  },
  
  // Download template as PDF
  downloadTemplate: async (id, lang = 'uz_latin') => {
    const response = await api.get(`/api/v1/legal/templates/${id}/download/`, {
      params: { lang },
      responseType: 'blob',
    })
    return response.data
  },
}

export default legalDatabaseService
