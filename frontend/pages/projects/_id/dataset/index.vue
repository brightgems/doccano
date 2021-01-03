<template>
  <v-card>
    <v-card-title class="mb-2">
      <document-action-menu />
      <document-deletion-button class="ms-2" />
      <document-assign-to class="ms-2" />
    </v-card-title>
    <document-list />
  </v-card>
</template>

<script>
import DocumentList from '@/components/containers/documents/DocumentList'
import DocumentActionMenu from '@/components/containers/documents/DocumentActionMenu'
import DocumentDeletionButton from '@/components/containers/documents/DocumentDeletionButton'
import DocumentAssignTo from '@/components/containers/documents/DocumentAssignTo'

export default {
  layout: 'project',

  components: {
    DocumentList,
    DocumentActionMenu,
    DocumentDeletionButton,
    DocumentAssignTo
  },

  validate({ params }) {
    return /^\d+$/.test(params.id)
  }
}
</script>
