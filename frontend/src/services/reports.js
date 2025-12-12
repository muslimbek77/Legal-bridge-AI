import api from './api'

export const reportsService = {
  // Get all reports
  getReports: async (params = {}) => {
    const response = await api.get('/api/v1/reports/', { params })
    return response.data
  },
  
  // Get single report
  getReport: async (id) => {
    const response = await api.get(`/api/v1/reports/${id}/`)
    return response.data
  },
  
  // Generate report for contract
  generateReport: async (contractId, format = 'pdf') => {
    const response = await api.post('/api/v1/reports/generate/', {
      contract_id: contractId,
      report_type: 'analysis',
      format,
    })
    return response.data
  },
  
  // Download report
  downloadReport: async (id) => {
    const response = await api.get(`/api/v1/reports/${id}/download/`, {
      responseType: 'blob',
    })
    return response.data
  },
  
  // Delete report
  deleteReport: async (id) => {
    await api.delete(`/api/v1/reports/${id}/`)
  },
  
  // Send report by email
  sendByEmail: async (id, email) => {
    const response = await api.post(`/api/v1/reports/${id}/send/`, { email })
    return response.data
  },
}

export default reportsService
