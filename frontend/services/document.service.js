import ApiService from '@/services/api.service'

class DocumentService {
  constructor() {
    this.request = ApiService
  }

  getDocumentList({ projectId, limit, offset, q = '', isChecked = '', filterName = '', assignedTo = '', approved = '' }) {
    return this.request.get(`/projects/${projectId}/docs?limit=${limit}&offset=${offset}&q=${q}&${filterName}=${isChecked}&assigned_to=${assignedTo}&approved=${approved}`)
  }

  addDocument(projectId, payload) {
    return this.request.post(`/projects/${projectId}/docs`, payload)
  }

  deleteDocument(projectId, docId) {
    return this.request.delete(`/projects/${projectId}/docs/${docId}`)
  }

  updateDocument(projectId, docId, payload) {
    return this.request.patch(`/projects/${projectId}/docs/${docId}`, payload)
  }

  uploadFile(projectId, payload, config = {}) {
    return this.request.post(`/projects/${projectId}/docs/upload`, payload, config)
  }

  assignDocumentsToMembers(projectId, payload) {
    return this.request.post(`/projects/${projectId}/docs/doc_assign_to`, payload)
  }

  exportFile(projectId, format) {
    const headers = {}
    if (format === 'csv') {
      headers.Accept = 'text/csv; charset=utf-8'
      headers['Content-Type'] = 'text/csv; charset=utf-8'
    } else {
      headers.Accept = 'application/json'
      headers['Content-Type'] = 'application/json'
    }
    const config = {
      responseType: 'blob',
      params: {
        q: format
      },
      headers
    }
    return this.request.get(`/projects/${projectId}/docs/download`, config)
  }

  approveDocument(projectId, docId, payload) {
    return this.request.post(`/projects/${projectId}/docs/${docId}/approve-labels`, payload)
  }

  getCommentList(projectId, docId) {
    return this.request.get(`/projects/${projectId}/docs/${docId}/comments`)
  }

  addComment(projectId, docId, payload) {
    return this.request.post(`/projects/${projectId}/docs/${docId}/comments`, payload)
  }

  deleteComment(projectId, docId, commentId) {
    return this.request.delete(`/projects/${projectId}/docs/${docId}/comments/${commentId}`)
  }

  updateComment(projectId, docId, commentId, payload) {
    return this.request.put(`/projects/${projectId}/docs/${docId}/comments/${commentId}`, payload)
  }
}

export default new DocumentService()
