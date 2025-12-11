import api from './api'

export const analysisService = {
  // Get all analysis results
  getAnalysisResults: async (params = {}) => {
    const response = await api.get('/api/v1/analysis/results/', { params })
    return response.data
  },
  
  // Get single analysis result
  getAnalysisResult: async (id) => {
    const response = await api.get(`/api/v1/analysis/results/${id}/`)
    return response.data
  },
  
  // Get analysis by contract
  getAnalysisByContract: async (contractId) => {
    const response = await api.get('/api/v1/analysis/results/', {
      params: { contract: contractId }
    })
    return response.data
  },
  
  // Get compliance issues
  getComplianceIssues: async (params = {}) => {
    const response = await api.get('/api/v1/analysis/issues/', { params })
    return response.data
  },
  
  // Update compliance issue
  updateIssue: async (id, data) => {
    const response = await api.patch(`/api/v1/analysis/issues/${id}/`, data)
    return response.data
  },
  
  // Submit feedback
  submitFeedback: async (analysisId, data) => {
    const response = await api.post('/api/v1/analysis/feedback/', {
      analysis: analysisId,
      ...data,
    })
    return response.data
  },
  
  // Get law references
  getLawReferences: async (params = {}) => {
    const response = await api.get('/api/v1/analysis/law-references/', { params })
    return response.data
  },
  
  // Get statistics
  getStatistics: async () => {
    const response = await api.get('/api/v1/analysis/statistics/')
    return response.data
  },
}

export default analysisService
