<template>
  <confirm-dialog
    :disabled="!isModelSelected"
    :items="selected"
    @ok="handleDeleteModel"
    title="Delete Model"
    message="Are you sure you want to delete these models?"
    item-key="name"
  />
</template>

<script>
import { mapState, mapGetters } from 'vuex'
import ConfirmDialog from '@/components/organisms/utils/ConfirmDialog'

export default {
  components: {
    ConfirmDialog
  },

  computed: {
    ...mapState('models', ['selected']),
    ...mapGetters('models', ['isModelSelected'])
  },

  methods: {
    handleDeleteModel() {
      this.$store.dispatch('models/deleteModel')
    }
  }
}
</script>
