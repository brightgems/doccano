import ApiService from '@/services/api.service'

class ModelService {
  constructor() {
    this.request = ApiService
  }

  getModelBackendList() {
    return this.request.get('/model_backends')
  }

  getModelList() {
    return this.request.get('/models')
  }

  createModel(data) {
    return this.request.post('/models', data)
  }

  updateModel(modelId, payload) {
    return this.request.patch(`/models/${modelId}`, payload)
  }

  deleteModel(modelId) {
    return this.request.delete(`/models/${modelId}`)
  }

  fetchModelById(modelId) {
    return this.request.get(`/models/${modelId}`)
  }
}

export default new ModelService()
