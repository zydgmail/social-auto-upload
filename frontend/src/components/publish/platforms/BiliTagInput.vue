<template>
  <div class="bili-tag-section">
    <div class="tag-display">
      <div class="selected-tags">
        <el-tag
          v-for="(tag, index) in selectedTags"
          :key="index"
          closable
          @close="removeTag(index)"
          class="tag-item"
          size="small"
        >
          {{ tag }}
        </el-tag>
      </div>
      <el-button 
        type="primary" 
        plain 
        @click="openTagDialog"
        class="add-tag-btn"
        size="small"
        :disabled="isTagLimitReached"
      >
        添加标签
      </el-button>
    </div>
    
    <!-- 标签数量提示 -->
    <div class="tag-tips">
      <el-text size="small" type="info">
        已添加 {{ selectedTags.length }}/10 个标签，标签有助于更多用户发现你的视频
      </el-text>
      <el-text v-if="isTagLimitReached" size="small" type="warning" style="margin-left: 8px;">
        已达上限
      </el-text>
    </div>
    
    <!-- 验证错误提示 -->
    <div v-if="errorMessage" class="error-message">
      <el-alert
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
        size="small"
      />
    </div>

    <!-- 添加标签弹窗 -->
    <el-dialog
      v-model="tagDialogVisible"
      title="添加标签"
      width="600px"
      class="tag-dialog"
    >
      <div class="tag-dialog-content">
        <!-- 自定义标签输入 -->
        <div class="custom-tag-input">
          <el-input
            v-model="customTag"
            placeholder="输入标签内容"
            class="custom-input"
            @keyup.enter="addCustomTag"
            maxlength="10"
            show-word-limit
          />
          <el-button type="primary" @click="addCustomTag">添加</el-button>
        </div>

        <!-- 推荐标签 -->
        <div class="recommended-tags">
          <h4>推荐标签</h4>
          <div class="tag-grid">
            <el-button
              v-for="tag in recommendedTags"
              :key="tag"
              :type="selectedTags.includes(tag) ? 'primary' : 'default'"
              @click="toggleRecommendedTag(tag)"
              class="tag-btn"
              size="small"
              :disabled="selectedTags.includes(tag) && isTagLimitReached"
            >
              {{ tag }}
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="tagDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmTagSelection">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  validateOnInput: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'validation-change'])

const selectedTags = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isTagLimitReached = computed(() => {
  return selectedTags.value.length >= 10  // B站标签上限为10个
})

const errorMessage = ref('')

// 弹窗状态
const tagDialogVisible = ref(false)
const customTag = ref('')

// B站推荐标签列表
const recommendedTags = [
  '知识', '游戏', '科技', '娱乐', '音乐', '舞蹈',
  '动画', '影视', '生活', '美食', '体育', '时尚',
  '汽车', '旅游', '动物', '搞笑', '教程', '测评',
  '开箱', 'vlog', '日常', '分享', '原创', '转载'
]

// 打开添加标签弹窗
const openTagDialog = () => {
  if (isTagLimitReached.value) {
    ElMessage.warning('最多只能添加10个标签')
    return
  }
  tagDialogVisible.value = true
}

// 验证单个标签
const validateSingleTag = (tag) => {
  if (!tag || tag.trim() === '') {
    return { valid: false, message: '标签内容不能为空' }
  }
  
  const trimmedTag = tag.trim()
  
  if (trimmedTag.length > 10) {
    return { valid: false, message: '单个标签不能超过10个字符' }
  }
  
  if (trimmedTag.length < 1) {
    return { valid: false, message: '标签至少需要1个字符' }
  }
  
  // 检查是否包含特殊字符
  const invalidChars = /[<>\/\\|:"*?#]/
  if (invalidChars.test(trimmedTag)) {
    return { valid: false, message: '标签不能包含特殊字符' }
  }
  
  return { valid: true, message: '' }
}

// 添加自定义标签
const addCustomTag = () => {
  if (!customTag.value.trim()) {
    ElMessage.warning('请输入标签内容')
    return
  }
  
  const validation = validateSingleTag(customTag.value.trim())
  if (!validation.valid) {
    ElMessage.error(validation.message)
    return
  }
  
  if (isTagLimitReached.value) {
    ElMessage.warning('最多只能添加10个标签')
    return
  }
  
  const trimmedTag = customTag.value.trim()
  if (!selectedTags.value.includes(trimmedTag)) {
    selectedTags.value.push(trimmedTag)
    customTag.value = ''
    ElMessage.success('标签添加成功')
    validateTagsInternal()
  } else {
    ElMessage.warning('标签已存在')
  }
}

// 切换推荐标签
const toggleRecommendedTag = (tag) => {
  if (isTagLimitReached.value && !selectedTags.value.includes(tag)) {
    ElMessage.warning('最多只能添加10个标签')
    return
  }
  
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
  validateTagsInternal()
}

// 删除标签
const removeTag = (index) => {
  selectedTags.value.splice(index, 1)
  validateTagsInternal()
}

// 确认添加标签
const confirmTagSelection = () => {
  tagDialogVisible.value = false
  customTag.value = ''
  ElMessage.success('添加标签完成')
}

// 验证标签
const validateTagsInternal = () => {
  if (props.validateOnInput) {
    let validation = { valid: true, message: '' }
    
    if (selectedTags.value.length === 0) {
      validation = { valid: false, message: '请至少添加一个标签' }
    } else if (selectedTags.value.length > 10) {
      validation = { valid: false, message: '最多只能添加10个标签' }
    } else {
      // 验证每个标签
      for (const tag of selectedTags.value) {
        const tagValidation = validateSingleTag(tag)
        if (!tagValidation.valid) {
          validation = tagValidation
          break
        }
      }
    }
    
    errorMessage.value = validation.valid ? '' : validation.message
    emit('validation-change', validation)
  }
}

// 手动验证方法
const validate = () => {
  let validation = { valid: true, message: '' }
  
  if (props.modelValue.length === 0) {
    validation = { valid: false, message: '请至少添加一个标签' }
  } else if (props.modelValue.length > 10) {
    validation = { valid: false, message: '最多只能添加10个标签' }
  } else {
    // 验证每个标签
    for (const tag of props.modelValue) {
      const tagValidation = validateSingleTag(tag)
      if (!tagValidation.valid) {
        validation = tagValidation
        break
      }
    }
  }
  
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
.bili-tag-section {
  .tag-display {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .selected-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      min-height: 24px;
      
      .tag-item {
        font-size: 13px;
        border-radius: 4px;
      }
    }
    
    .add-tag-btn {
      align-self: flex-start;
      font-size: 13px;
      height: 28px;
      padding: 0 12px;
    }
  }
  
  .tag-tips {
    margin-top: 8px;
  }
  
  .error-message {
    margin-top: 8px;
  }
  
  .tag-dialog-content {
    .custom-tag-input {
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      
      .custom-input {
        flex: 1;
      }
    }
    
    .recommended-tags {
      h4 {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 500;
        color: #303133;
      }
      
      .tag-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
        gap: 8px;
        
        .tag-btn {
          height: 32px;
          font-size: 13px;
          border-radius: 4px;
          min-width: 80px;
          padding: 0 8px;
          white-space: nowrap;
          text-align: center;
          display: flex;
          align-items: center;
          justify-content: center;
          
          &.el-button--primary {
            background-color: #00a1d6;
            border-color: #00a1d6;
            color: white;
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
