<template>
  <div>
    <v-text-field
      v-model="searchText"
      @change="search"
      solo
      clearable
      label="Search documents"
      prepend-icon="fas fa-search"
    />
  </div>
</template>
<script>
import { mapMutations, mapActions } from 'vuex'

export default {
  data() {
    return {
      searchText: ''
    }
  },
  methods: {
    ...mapActions('documents', ['getDocumentList']),
    ...mapActions('pagination', ['resetPage']),
    ...mapMutations('documents', ['setCurrent', 'updateSearchOptions', 'setCurrent']),
    search() {
      this.updateSearchOptions({
        q: this.searchText || ''
      })
      this.getDocumentList({
        projectId: this.$route.params.id
      }).then((response) => {
        this.setCurrent(0)
        this.resetPage({ projectId: this.$route.params.id })
      })
    }
  }
}
</script>
