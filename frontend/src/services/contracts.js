import api from './api'

export const contractsService = {
  // Get all contracts with pagination and filters
  getContracts: async (params = {}) => {
    const response = await api.get('/api/v1/contracts/', { params })
    return response.data
  },
  
  // Get single contract
  getContract: async (id) => {
    const response = await api.get(`/api/v1/contracts/${id}/`)
    return response.data
  },
  
  // Upload new contract
  uploadContract: async (formData) => {
    const response = await api.post('/api/v1/contracts/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
  
  // Update contract
  updateContract: async (id, data) => {
    const response = await api.patch(`/api/v1/contracts/${id}/`, data)
    return response.data
  },
  
  // Delete contract
  deleteContract: async (id) => {
    await api.delete(`/api/v1/contracts/${id}/`)
  },
  
  // Start analysis
  analyzeContract: async (id) => {
    const response = await api.post(`/api/v1/contracts/${id}/analyze/`)
    return response.data
  },
  
  // Get contract statistics
  getStatistics: async () => {
    const response = await api.get('/api/v1/contracts/stats/')
    return response.data
  },
  
  // Get contract sections
  getSections: async (contractId) => {
    const response = await api.get(`/api/v1/contracts/sections/`, {
      params: { contract: contractId }
    })
    return response.data
  },
  
  // Get contract clauses
  getClauses: async (contractId) => {
    const response = await api.get(`/api/v1/contracts/clauses/`, {
      params: { contract: contractId }
    })
    return response.data
  },
  
  // Add comment
  addComment: async (contractId, content) => {
    const response = await api.post('/api/v1/contracts/comments/', {
      contract: contractId,
      content,
    })
    return response.data
  },
  
  // Get comments
  getComments: async (contractId) => {
    const response = await api.get('/api/v1/contracts/comments/', {
      params: { contract: contractId }
    })
    return response.data
  },
}

export default contractsService
