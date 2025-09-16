<template>
  <div class="title-section">
    <h3>标题</h3>
    <el-input
      v-model="title"
      type="textarea"
      :rows="3"
      :placeholder="placeholder"
      :maxlength="maxLength"
      show-word-limit
      class="title-input"
      @input="handleInput"
    />
    
    <!-- 验证错误提示 -->
    <div v-if="errorMessage" class="error-message">
      <el-alert
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
        class="error-alert"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { getPlatformConfig, validateTitle } from '@/utils/platformConfig'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  platformKey: {
    type: Number,
    required: true
  },
  validateOnInput: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'validation-change'])

const platformConfig = computed(() => getPlatformConfig(props.platformKey))

const title = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const placeholder = computed(() => platformConfig.value.titlePlaceholder)
const maxLength = computed(() => platformConfig.value.titleLimit)

const errorMessage = ref('')

const handleInput = (value) => {
  if (props.validateOnInput) {
    const validation = validateTitle(value, props.platformKey)
    errorMessage.value = validation.valid ? '' : validation.message
    emit('validation-change', validation)
  }
}

// 手动验证方法
const validate = () => {
  const validation = validateTitle(props.modelValue, props.platformKey)
  errorMessage.value = validation.valid ? '' : validation.message
  emit('validation-change', validation)
  return validation
}

// 暴露验证方法给父组件
defineExpose({
  validate
})
</script>

<style lang="scss" scoped>
.title-section {
  margin-bottom: 30px;
  
  h3 {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin: 0 0 10px 0;
  }
  
  .title-input {
    max-width: 600px;
  }
  
  .error-message {
    margin-top: 10px;
    
    .error-alert {
      font-size: 13px;
    }
  }
}
</style>
