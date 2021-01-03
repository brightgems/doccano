<template>
  <base-modal
    :disabled="!isModelSelected"
    :is-create="false"
    text="Edit"
  >
    <template v-slot="slotProps">
      <model-creation-form
        :model="currentModel"
        :submit="updateModel"
        :is-create="false"
        @close="slotProps.close"
      />
    </template>
  </base-modal>
</template>
<script>
import { mapGetters, mapActions } from 'vuex'
import BaseModal from '@/components/molecules/BaseModal'
import ModelCreationForm from '@/components/organisms/models/ModelCreationForm'

export default {
  components: {
    BaseModal,
    ModelCreationForm
  },
  computed: {
    ...mapGetters('models', ['isModelSelected']),
    ...mapGetters('models', ['currentModel'])
  },
  methods: {
    ...mapActions('models', ['updateModel'])
  }
}
</script>
