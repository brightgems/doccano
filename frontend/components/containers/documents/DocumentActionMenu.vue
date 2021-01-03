<template>
  <div>
    <action-menu
      :items="menuItems"
      @upload="importDialog=true"
      @download="exportDialog=true"
      @delete-all="deleteDialog=true"
    />
    <base-dialog :dialog="importDialog">
      <document-upload-form
        :upload-document="uploadDocument"
        :formats="getImportFormat"
        @close="importDialog=false"
      />
    </base-dialog>
    <base-dialog :dialog="exportDialog">
      <document-export-form
        :export-document="exportDocument"
        :formats="getExportFormat"
        @close="exportDialog=false"
      />
    </base-dialog>
    <base-dialog :dialog="deleteDialog">
      <confirm-form
        :items="[]"
        @ok="deleteAllDocuments($route.params.id);deleteDialog=false"
        @cancel="deleteDialog=false"
        title="Delete All Documents"
        message="Are you sure you want to delete all the documents from this project?"
        item-key="text"
      />
    </base-dialog>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import ActionMenu from '@/components/molecules/ActionMenu'
import BaseDialog from '@/components/molecules/BaseDialog'
import ConfirmForm from '@/components/organisms/utils/ConfirmForm'
import DocumentUploadForm from '@/components/organisms/documents/DocumentUploadForm'
import DocumentExportForm from '@/components/organisms/documents/DocumentExportForm'

export default {
  components: {
    ActionMenu,
    BaseDialog,
    ConfirmForm,
    DocumentUploadForm,
    DocumentExportForm
  },

  data() {
    return {
      importDialog: false,
      exportDialog: false,
      deleteDialog: false,
      menuItems: [
        { title: 'Import Dataset', icon: 'mdi-upload', event: 'upload' },
        { title: 'Export Dataset', icon: 'mdi-download', event: 'download' },
        { title: 'Delete All', icon: 'mdi-delete  ', event: 'delete-all' }
      ]
    }
  },

  computed: {
    ...mapGetters('projects', ['getImportFormat', 'getExportFormat'])
  },

  created() {
    this.setCurrentProject(this.$route.params.id)
  },

  methods: {
    ...mapActions('documents', ['uploadDocument', 'exportDocument', 'deleteAllDocuments']),
    ...mapActions('projects', ['setCurrentProject'])
  }
}
</script>
