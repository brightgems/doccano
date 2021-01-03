<template>
  <div>
    <v-btn @click="dialog=true" class="text-capitalize" outlined>
      Assgin To
    </v-btn>
    <base-dialog :dialog="dialog">
      <base-card
        :disabled="!valid"
        @agree="createAssignments"
        @cancel="cancelAssignments"
        title="Assign annotations to member"
        agree-text="Confirm"
        cancel-text="Cancel"
      >
        <template #content>
          <v-data-table
            :value="selected"
            :headers="headers"
            :items="items"
            :search="search"
            :loading="loading"
            @input="updateSelected"
            loading-text="Loading... Please wait"
            item-key="id"
            show-select
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
          </v-data-table>
        </template>
      </base-card>
    </base-dialog>
  </div>
</template>
<script>
import { mapState, mapGetters, mapActions, mapMutations } from 'vuex'
import BaseDialog from '@/components/molecules/BaseDialog'
import BaseCard from '@/components/molecules/BaseCard'

export default {
  components: {
    BaseDialog,
    BaseCard
  },
  data() {
    return {
      dialog: false,
      headers: [
        {
          text: 'Name',
          align: 'left',
          sortable: false,
          value: 'username'
        },
        {
          text: 'Role',
          value: 'rolename'
        }
      ],
      search: ''
    }
  },
  computed: {
    ...mapState('members', ['items', 'selected', 'loading']),
    ...mapGetters('roles', ['roles']),
    valid() {
      console.log(this.selected.length > 0)
      return this.selected.length > 0
    }
  },
  created() {
    this.getMemberList({
      projectId: this.$route.params.id
    })
  },
  methods: {
    ...mapActions('members', ['getMemberList']),
    ...mapMutations('members', ['updateSelected']),
    ...mapActions('documents', ['assignDocumentsToMembers']),
    createAssignments() {
      const projectId = this.$route.params.id
      const users = this.selected.map(obj => obj.user)
      const payload = { projectId: projectId, users: users }
      this.assignDocumentsToMembers(payload).finally(() => {
        this.dialog = false
      })
    },
    cancelAssignments() {
      this.dialog = false
    }
  }
}
</script>
