<template>
  <div style="max-width:300px;">
    <v-overflow-btn
      :items="projectMembers"
      :menu-props="{maxWidht:150}"
      :value="selectedPerson"
      @change="changePerson"
      label="Assigned To"
      hide-details
      clearable
      dense
    >
      <template v-slot:prepend-inner>
        <v-icon>person</v-icon>
      </template>
    </v-overflow-btn>
  </div>
</template>

<script>
import { mapState, mapActions, mapMutations } from 'vuex'

export default {
  data() {
    return {
      selectedPerson: ''
    }
  },
  computed: {
    ...mapState('members', ['items']),
    projectMembers() {
      return this.items.map((member) => { return { text: member.username, value: member.user } })
    }
  },
  created() {
    this.getMemberList({
      projectId: this.$route.params.id
    })
  },
  methods: {
    ...mapActions('members', ['getMemberList']),
    ...mapActions('documents', ['getDocumentList']),
    ...mapActions('pagination', ['resetPage']),
    ...mapMutations('documents', ['updateSearchOptions', 'setCurrent']),
    changePerson(value) {
      this.updateSearchOptions({ assignedTo: value })
      this.getDocumentList({
        projectId: this.$route.params.id
      }).then((response) => {
        this.setCurrent(0)
        this.resetPage({ projectId: this.$route.params.id })
      })
    }
  }
}
</script>
<style lang="stylus">
.v-overflow-btn{
    margin-top: 0px;
}
.v-input__prepend-inner i{
    margin-top: 6px;
}
.v-overflow-btn .v-input__slot{
    border-width:0px;
}
</style>
