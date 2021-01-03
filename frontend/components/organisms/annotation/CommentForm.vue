<template>
  <v-card
    class="mx-auto"
  >
    <v-card-title>
      Comment History
      <v-spacer />
      <v-btn
        @click.stop="onEditComment(null)"
        color="primary"
        dark
      >
        <v-icon>mdi-plus</v-icon>New
      </v-btn>
      <v-dialog v-model="dialog" persistent max-width="590">
        <v-card>
          <v-card-title class="headline">
            Have any comments on current annotation?
          </v-card-title>
          <v-card-text>
            <v-textarea
              v-model="commentText"
              :rules="[rules.required, rules.counter]"
              outlined
              label="Input comments"
              maxlength="1000"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn @click="doSaveComment" :disabled="!isFormValid" color="green darken-1" text>
              Save
            </v-btn>
            <v-btn @click="dialog = false" color="yellow darken-1" text>
              Cancel
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-spacer />
      <v-btn
        @click="show = !show"
        icon
      >
        <v-icon>{{ show ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
      </v-btn>
    </v-card-title>
    <v-divider />
    <v-expand-transition>
      <div v-show="show">
        <v-card-text>
          <comment-list v-if="currentDoc && currentDoc.comments.length>0" :doEditComment="onEditComment" :doDeleteComment="doDeleteComment" />
          <div v-else class="text-center  pt-1">
            no comments
          </div>
        </v-card-text>
      </div>
    </v-expand-transition>
  </v-card>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import CommentList from '~/components/containers/annotation/CommentList'

export default {
  components: { CommentList },
  data() {
    return {
      // show comment list
      show: true,
      //   show dialog
      dialog: false,
      dialogState: 'new',
      dialogCommentId: null,
      commentText: '',
      rules: {
        required: value => !!value || 'Required.',
        counter: value => value.length <= 1000 || 'Max 1000 characters'
      }
    }
  },
  computed: {
    ...mapGetters('documents', ['currentDoc']),
    isFormValid() {
      return this.commentText
    }
  },
  methods: {
    ...mapActions('documents', ['addComment', 'deleteComment', 'updateComment']),
    onEditComment(commentId) {
      if (!commentId) {
        this.commentText = ''
      } else {
        // modify
        this.dialogCommentId = commentId
        this.commentText = this.currentDoc.comments.filter((o) => { return o.id === commentId })[0].text
      }
      this.dialog = true
    },
    doSaveComment() {
      if (!this.commentText) {
        return
      }
      if (this.dialogCommentId) {
        // update
        const payload = { projectId: this.$route.params.id, commentId: this.dialogCommentId, text: this.commentText }
        this.updateComment(payload)
      } else {
        // add
        console.log({ text: this.commentText })
        const payload = { projectId: this.$route.params.id, text: this.commentText }
        this.addComment(payload)
      }
      this.dialog = false
    },
    doDeleteComment(commentId) {
      const payload = { projectId: this.$route.params.id, commentId: commentId }
      this.deleteComment(payload)
    }
  }
}
</script>
