<template>
  <v-timeline :dense="$vuetify.breakpoint.smAndDown">
    <v-timeline-item
      v-for="(obj, index) in currentDoc.comments"
      :key="index"
      :right="index % 2==0"
      :left="index % 2==1"
      color="purple lighten-2"
      fill-dot
    >
      <v-card>
        <v-card-title class="purple lighten-2">
          <v-icon dark size="42" class="mr-4">
            mdi-message-text
          </v-icon>
          <h2 class="h6 white--text font-weight-light">
            {{ obj.username }}
          </h2>

          <v-spacer />
          <h2 class="subtitle-1 white--text font-weight-light pl-2">
            updated at {{ obj.updated_at|dateParse |dateFormat('HH:mm:ss MMM DD') }}
          </h2>
          <v-menu bottom left class="z-index:999">
            <template v-slot:activator="{ on, attrs }">
              <v-btn
                v-bind="attrs"
                v-on="on"
                dark
                icon
              >
                <v-icon>mdi-dots-vertical</v-icon>
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="doEditComment(obj.id)">
                <v-list-item-title>Edit</v-list-item-title>
              </v-list-item>
              <v-list-item @click="doDeleteComment(obj.id)">
                <v-list-item-title>Remvoe</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-card-title>
        <v-container>
          <v-row>
            <v-col
              cols="12"
              md="10"
            >
              <pre>{{ obj.text }} </pre>
            </v-col>
          </v-row>
        </v-container>
      </v-card>
    </v-timeline-item>
  </v-timeline>
</template>
<script>
import { mapGetters } from 'vuex'

export default {
  props: {
    doEditComment: {
      type: Function,
      default: () => ([]),
      required: true
    },
    doDeleteComment: {
      type: Function,
      default: () => ([]),
      required: true
    }
  },
  computed: {
    ...mapGetters('documents', ['currentDoc'])
  },
  created() {
    console.log(this.currentDoc)
  }

}
</script>
