<template>
  <v-card>
    <v-card-title>
      <model-creation-button />
      <model-edit-button />
      <model-deletion-button />
    </v-card-title>
    <model-list />
  </v-card>
</template>

<script>
import ModelList from '@/components/containers/models/ModelList'
import ModelDeletionButton from '@/components/containers/models/ModelDeletionButton'
import ModelCreationButton from '@/components/containers/models/ModelCreationButton'
import ModelEditButton from '@/components/containers/models/ModelEditButton'

export default {
  layout: 'models',
  middleware: ['check-auth', 'auth'],
  components: {
    ModelList,
    ModelCreationButton,
    ModelEditButton,
    ModelDeletionButton
  }
}
</script>
