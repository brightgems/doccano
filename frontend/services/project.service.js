import ApiService from '@/services/api.service'

class ProjectService {
  constructor() {
    this.request = ApiService
  }

  getProjectList() {
    return this.request.get('/projects')
  }

  createProject(data) {
    return this.request.post('/projects', data)
  }

  updateProject(projectId, payload) {
    return this.request.patch(`/projects/${projectId}`, payload)
  }

  deleteProject(projectId) {
    return this.request.delete(`/projects/${projectId}`)
  }

  deleteAllDocuments(projectId) {
    return this.request.post(`/projects/${projectId}/delete_all_documents`)
  }

  fetchProjectById(projectId) {
    return this.request.get(`/projects/${projectId}`)
  }
}

export default new ProjectService()
