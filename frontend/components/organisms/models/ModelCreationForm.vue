<template>
  <base-card
    :disabled="!valid"
    @agree="create"
    @cancel="cancel"
    title="Add Model"
    agree-text="Create"
    cancel-text="Cancel"
  >
    <template #content>
      <v-form
        ref="form"
        v-model="valid"
      >
        <v-text-field
          v-model="model.name"
          :rules="modelNameRules"
          label="Model name"
          prepend-icon="mdi-account-multiple"
          data-test="model-name"
          required
          autofocus
        />
        <v-text-field
          v-model="model.description"
          :rules="descriptionRules"
          label="Description"
          prepend-icon="mdi-clipboard-text"
          data-test="model-description"
          required
        />
        <v-select
          v-model="model.model_type"
          :items="getProjectTypes"
          :rules="modelTypeRules"
          item-text="name"
          item-value="id"
          label="Model Type"
          prepend-icon="mdi-keyboard"
          data-test="model-type"
          required
        />
        <v-select
          v-model="model.model_backend"
          :items="modelBackends"
          :rules="modelBackendRules"
          item-text="name"
          item-value="id"
          label="Model Backend"
          prepend-icon="mdi-keyboard"
          data-test="model-backend"
          required
        />
        <v-select
          v-model="model.target_project"
          :items="sourceProjects"
          :rules="sourceProjectRules"
          @change="onChangeSourceProject"
          item-text="name"
          item-value="id"
          label="Target Project"
          prepend-icon="mdi-keyboard"
          data-test="target-project"
          required
        />
        <v-select
          v-model="model.predict_labels"
          :items="labels"
          :rules="modelLabelRules"
          item-text="text"
          item-value="id"
          label="Predict Labels"
          prepend-icon="mdi-keyboard"
          data-test="source-project"
          required
          multiple
        />
      </v-form>
    </template>
  </base-card>
</template>

<script>
import { mapState, mapGetters } from 'vuex'
import BaseCard from '@/components/molecules/BaseCard'
import { modelNameRules, descriptionRules, sourceProjectRules, modelTypeRules, modelLabelRules, modelBackendRules } from '@/rules/index'

export default {
  components: {
    BaseCard
  },
  props: {
    model: {
      type: Object,
      default: () => {
        return {
          name: '',
          description: '',
          model_type: null,
          model_backend: null,
          target_project: null,
          predict_labels: []
        }
      }
    },
    isCreate: {
      type: Boolean,
      default: false
    },
    submit: {
      type: Function,
      default: () => { },
      required: true
    },
    modelTypes: {
      type: Array,
      default: () => [
        'Text Classification',
        'Sequence Labeling',
        'Sequence to sequence'
      ] // Todo: Get model types from backend server.
    }
  },
  data() {
    return {
      valid: false,
      modelNameRules,
      sourceProjectRules,
      descriptionRules,
      modelLabelRules,
      modelTypeRules,
      modelBackendRules
    }
  },
  computed: {
    ...mapState('projects', ['projects']),
    ...mapState('models', ['modelBackendList']),
    ...mapState('labels', {
      labels(state) {
        return state.items
      }
    }),
    ...mapGetters('projects', ['getProjectTypes']),
    sourceProjects() {
      const ret = this.projects.filter(project =>
        project.project_type === this.model.model_type
      )
      return ret
    },
    modelBackends() {
      const ret = this.modelBackendList.filter(backend =>
        backend.model_type === this.model.model_type
      )
      return ret
    }
  },
  async created() {
    await this.$store.dispatch('models/getModelBackendList')
    await this.$store.dispatch('projects/getProjectList')
  },
  methods: {
    cancel() {
      this.$emit('close')
    },
    validate() {
      return this.$refs.form.validate()
    },
    reset() {
      this.$refs.form.reset()
    },
    create() {
      if (this.validate()) {
        this.submit({
          name: this.model.name,
          description: this.model.description,
          model_type: this.model.model_type,
          model_backend: this.model.model_backend,
          target_project: this.model.target_project,
          predict_labels: this.model.predict_labels
        })
        this.reset()
        this.cancel()
      }
    },
    onChangeSourceProject() {
      this.$store.dispatch('labels/getLabelList', { projectId: this.model.target_project })
    }
  }
}
</script>
