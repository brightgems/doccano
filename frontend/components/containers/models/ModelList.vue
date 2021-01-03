<template>
  <v-data-table
    :value="selected"
    :headers="headers"
    :items="models"
    :search="search"
    :loading="loading"
    @input="update"
    loading-text="Loading... Please wait"
    item-key="id"
    show-select
    single-select
  >
    <template v-slot:top>
      <v-text-field
        v-model="search"
        prepend-inner-icon="search"
        label="Search"
        single-line
        hide-details
        filled
      />
    </template>
    <template v-slot:item.name="{ item }">
      <nuxt-link :to="`/models/${item.id}`">
        <span>{{ item.name }}</span>
      </nuxt-link>
    </template>
  </v-data-table>
</template>

<script>
import { mapState, mapActions, mapMutations } from 'vuex'

export default {
  data() {
    return {
      search: '',
      headers: [
        {
          text: 'Name',
          align: 'left',
          value: 'name'
        },
        {
          text: 'Description',
          value: 'description'
        },
        {
          text: 'Type',
          value: 'model_type'
        }
      ]
    }
  },
  computed: {
    ...mapState('models', ['models', 'selected', 'loading'])

  },
  async created() {
    await this.getModelList()
  },
  methods: {
    ...mapActions('models', ['getModelList']),
    ...mapMutations('models', ['updateSelected']),

    update(selected) {
      this.updateSelected(selected)
    }
  }
}
</script>
