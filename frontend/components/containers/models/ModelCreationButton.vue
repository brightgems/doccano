<template>
  <base-modal
    :is-create="true"
    text="Create"
  >
    <template v-slot="slotProps">
      <model-creation-form
        :model="model"
        :submit="createModel"
        :is-create="true"
        @close="slotProps.close"
      />
    </template>
  </base-modal>
</template>
<script>
import { mapActions } from 'vuex'
import BaseModal from '@/components/molecules/BaseModal'
import ModelCreationForm from '@/components/organisms/models/ModelCreationForm'

export default {
  components: {
    BaseModal,
    ModelCreationForm
  },
  data() {
    return {
      model: {
        name: '',
        description: '',
        model_type: null,
        model_backend: null,
        target_project: null,
        predict_labels: []
      }
    }
  },
  methods: {
    ...mapActions('models', ['createModel'])
  }
}
</script>
