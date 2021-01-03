import ModelService from '@/services/model.service'

export const state = () => ({
  models: [],
  modelBackendList: [],
  selected: [],
  current: {},
  loading: false
})

export const getters = {
  isModelSelected(state) {
    return state.selected.length > 0
  },
  currentModel(state) {
    return state.current
  },
  getCurrentUserRole(state) {
    return state.current.current_users_role || {}
  }
}

export const mutations = {
  setModelList(state, payload) {
    state.models = payload
  },
  createModel(state, model) {
    state.models.unshift(model)
  },
  updateModel(state, model) {
    const item = state.models.find(item => item.id === model.id)
    Object.assign(item, model)
  },
  deleteModel(state, modelId) {
    state.models = state.models.filter(item => item.id !== modelId)
  },
  updateSelected(state, selected) {
    state.selected = selected
  },
  resetSelected(state) {
    state.selected = []
  },
  setLoading(state, payload) {
    state.loading = payload
  },
  setCurrent(state, payload) {
    state.current = payload
  },
  setModelBackendList(state, payload) {
    state.modelBackendList = payload
  }
}

export const actions = {
  getModelBackendList({ commit }) {
    ModelService.getModelBackendList()
      .then((response) => {
        commit('setModelBackendList', response.data)
      })
      .catch((error) => {
        alert(error)
      })
  },
  getModelList({ commit }, config) {
    commit('setLoading', true)
    ModelService.getModelList()
      .then((response) => {
        commit('setModelList', response.data)
      })
      .catch((error) => {
        alert(error)
      })
      .finally(() => {
        commit('setLoading', false)
      })
  },
  createModel({ commit }, model) {
    ModelService.createModel(model)
      .then((response) => {
        commit('createModel', response.data)
      })
      .catch((error) => {
        alert(error)
      })
  },
  updateModel({ commit }, data) {
    ModelService.updateModel(data.modelId, data)
      .then((response) => {
        commit('updateModel', response.data)
      })
      .catch((error) => {
        alert(error)
      })
  },
  deleteModel({ commit, state }, config) {
    for (const model of state.selected) {
      ModelService.deleteModel(model.id)
        .then((response) => {
          commit('deleteModel', model.id)
        })
        .catch((error) => {
          alert(error)
        })
    }
    commit('resetSelected')
  },
  setCurrentModel({ commit }, modelId) {
    return ModelService.fetchModelById(modelId)
      .then((response) => {
        commit('setCurrent', response.data)
      })
      .catch((error) => {
        alert(error)
      })
  },
  updateCurrentModel({ commit }, data) {
    ModelService.updateModel(data.modelId, data)
      .then((response) => {
        commit('setCurrent', response.data)
      })
      .catch((error) => {
        alert(error)
      })
  }
}
