// Rules for project label.
export const colorRules = [
  v => !!v || 'Color is required'
]

export const labelNameRules = [
  v => !!v || 'Label name is required',
  v => (v && v.length <= 30) || 'Label name must be less than 30 characters'
]

// Rules for project member.
export const userNameRules = [
  v => !!v || 'User name is required',
  v => (v && v.length <= 30) || 'User name must be less than 30 characters'
]

export const roleRules = [
  v => !!v || 'Role is required'
]

// Rules for a project.
export const projectNameRules = [
  v => !!v || 'Project name is required',
  v => (v && v.length <= 30) || 'Project name must be less than 30 characters'
]

export const descriptionRules = [
  v => !!v || 'Description is required',
  v => (v && v.length <= 100) || 'Description must be less than 100 characters'
]

export const projectTypeRules = [
  v => !!v || 'Project type is required'
]

// Rules for Document.
export const fileFormatRules = [
  v => !!v || 'File format is required'
]

export const uploadFileRules = [
  v => !!v || 'File is required',
  v => !v || v.size < 50000000 || 'File size should be less than 10 MB!'
]

// Rules for user.
export const passwordRules = [
  v => !!v || 'Password is required',
  v => (v && v.length <= 30) || 'Password must be less than 30 characters'
]

// Rules for models

export const modelNameRules = [
  v => !!v || 'Project name is required',
  v => (v && v.length <= 30) || 'Model name must be less than 30 characters'
]

export const sourceProjectRules = [
  v => !!v || 'Source project is required'
]

export const modelTypeRules = [
  v => !!v || 'Model Type is required'
]

export const modelLabelRules = [
  v => !!v || 'Labels is required'
]

export const modelBackendRules = [
  v => !!v || 'Model Backend is required'
]
