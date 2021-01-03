<template>
  <v-card>
    <edit-text-button />
    <v-card-text class="title">
      <entity-item-box />
    </v-card-text>
  </v-card>
</template>

<script>
import EntityItemBox from '~/components/containers/annotation/EntityItemBox'
import EditTextButton from '~/components/containers/annotation/EditTextButton'

export default {
  layout: 'annotation',

  components: {
    EntityItemBox,
    EditTextButton
  }
}
</script>
