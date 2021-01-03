<template>
  <v-dialog v-model="dialog" persistent max-width="600px">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        v-bind="attrs"
        v-on="on"
        @click="showDialog"
        fab
        dark
        small
        class="float-btn"
        color="primary"
      >
        <v-icon>mdi-pencil</v-icon>
      </v-btn>
    </template>
    <v-card>
      <v-card-title>
        <span class="headline">Edit Document</span>
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-textarea
          ref="editor"
          v-if="currentDoc"
          v-model="text"
          @change="onChangeText"
          outlined
          auto-grow
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="dialog = false" color="blue darken-1" text>
          Close
        </v-btn>
        <v-btn @click="dialog = false;doUpdateDocument()" color="blue darken-1" text>
          Save
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  data() {
    return {
      dialog: false,
      text: ''
    }
  },
  computed: {
    ...mapGetters('documents', ['currentDoc'])
  },
  methods: {
    ...mapActions('documents', ['updateDocument']),
    showDialog() {
      this.text = this.currentDoc.text
    },
    doUpdateDocument() {
      const payload = { projectId: this.$route.params.id, id: this.currentDoc.id, text: this.text }
      this.updateDocument(payload)
    },
    onChangeText(event) {
      console.log(event)
    }
  }
}
</script>
<style scoped>
.float-btn {
  float: right;
  position: relative;
  top: -20px;
  margin-right: 10px;
}
</style>
