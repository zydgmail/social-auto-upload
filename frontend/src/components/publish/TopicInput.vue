<template>
  <div class="topic-section">
    <h3>话题</h3>
    <div class="topic-display">
      <div class="selected-topics">
        <el-tag
          v-for="(topic, index) in selectedTopics"
          :key="index"
          closable
          @close="removeTopic(index)"
          class="topic-tag"
        >
          #{{ topic }}
        </el-tag>
      </div>
      <el-button 
        type="primary" 
        plain 
        @click="openTopicDialog"
        class="select-topic-btn"
        :disabled="isTopicLimitReached"
      >
        添加话题
      </el-button>
    </div>
    
    <!-- 话题数量提示 -->
    <div v-if="platformConfig" class="topic-tips">
      <el-alert
        :title="`已添加 ${selectedTopics.length}/${platformConfig.topicLimit} 个话题`"
        :type="isTopicLimitReached ? 'warning' : 'info'"
        :closable="false"
        show-icon
        class="topic-alert"
      />
    </div>
    
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

    <!-- 添加话题弹窗 -->
    <el-dialog
      v-model="topicDialogVisible"
      title="添加话题"
      width="600px"
      class="topic-dialog"
    >
      <div class="topic-dialog-content">
        <!-- 自定义话题输入 -->
        <div class="custom-topic-input">
          <el-input
            v-model="customTopic"
            placeholder="输入自定义话题"
            class="custom-input"
            @keyup.enter="addCustomTopic"
          >
            <template #prepend>#</template>
          </el-input>
          <el-button type="primary" @click="addCustomTopic">添加</el-button>
        </div>

        <!-- 推荐话题 -->
        <div class="recommended-topics">
          <h4>推荐话题</h4>
          <div class="topic-grid">
            <el-button
              v-for="topic in recommendedTopics"
              :key="topic"
              :type="selectedTopics.includes(topic) ? 'primary' : 'default'"
              @click="toggleRecommendedTopic(topic)"
              class="topic-btn"
              :disabled="selectedTopics.includes(topic) && isTopicLimitReached"
            >
              {{ topic }}
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="topicDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmTopicSelection">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getPlatformConfig, validateTopics, validateSingleTopic } from '@/utils/platformConfig'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
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

const selectedTopics = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isTopicLimitReached = computed(() => {
  return selectedTopics.value.length >= platformConfig.value.topicLimit
})

const errorMessage = ref('')

// 弹窗状态
const topicDialogVisible = ref(false)
const customTopic = ref('')

// 推荐话题列表
const recommendedTopics = [
  '游戏', '知识', '自动化', '系统平台', '自媒体工具', '跨境电商',
  '科技', '教程', '云手机平台', '云电脑平台', '脚本', '开源',
  '健康', '时尚', '美妆', '摄影', '宠物', '汽车'
]

// 打开添加话题弹窗
const openTopicDialog = () => {
  if (isTopicLimitReached.value) {
    ElMessage.warning(`最多只能添加${platformConfig.value.topicLimit}个话题`)
    return
  }
  topicDialogVisible.value = true
}

// 添加自定义话题
const addCustomTopic = () => {
  if (!customTopic.value.trim()) {
    ElMessage.warning('请输入话题内容')
    return
  }
  
  const validation = validateSingleTopic(customTopic.value.trim())
  if (!validation.valid) {
    ElMessage.error(validation.message)
    return
  }
  
  if (isTopicLimitReached.value) {
    ElMessage.warning(`最多只能添加${platformConfig.value.topicLimit}个话题`)
    return
  }
  
  if (!selectedTopics.value.includes(customTopic.value.trim())) {
    selectedTopics.value.push(customTopic.value.trim())
    customTopic.value = ''
    ElMessage.success('话题添加成功')
    validateTopicsInternal()
  } else {
    ElMessage.warning('话题已存在')
  }
}

// 切换推荐话题
const toggleRecommendedTopic = (topic) => {
  if (isTopicLimitReached.value && !selectedTopics.value.includes(topic)) {
    ElMessage.warning(`最多只能添加${platformConfig.value.topicLimit}个话题`)
    return
  }
  
  const index = selectedTopics.value.indexOf(topic)
  if (index > -1) {
    selectedTopics.value.splice(index, 1)
  } else {
    selectedTopics.value.push(topic)
  }
  validateTopicsInternal()
}

// 删除话题
const removeTopic = (index) => {
  selectedTopics.value.splice(index, 1)
  validateTopicsInternal()
}

// 确认添加话题
const confirmTopicSelection = () => {
  topicDialogVisible.value = false
  customTopic.value = ''
  ElMessage.success('添加话题完成')
}

// 验证话题
const validateTopicsInternal = () => {
  if (props.validateOnInput) {
    const validation = validateTopics(selectedTopics.value, props.platformKey)
    errorMessage.value = validation.valid ? '' : validation.message
    emit('validation-change', validation)
  }
}

// 手动验证方法
const validate = () => {
  const validation = validateTopics(props.modelValue, props.platformKey)
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
.topic-section {
  margin-bottom: 30px;
  
  h3 {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin: 0 0 10px 0;
  }
  
  .topic-display {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .selected-topics {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      min-height: 32px;
      
      .topic-tag {
        font-size: 14px;
      }
    }
    
    .select-topic-btn {
      align-self: flex-start;
    }
  }
  
  .topic-tips {
    margin-top: 10px;
    
    .topic-alert {
      font-size: 13px;
    }
  }
  
  .error-message {
    margin-top: 10px;
    
    .error-alert {
      font-size: 13px;
    }
  }
  
  .topic-dialog-content {
    .custom-topic-input {
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      
      .custom-input {
        flex: 1;
      }
    }
    
    .recommended-topics {
      h4 {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 500;
        color: #303133;
      }
      
      .topic-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 12px;
        
        .topic-btn {
          height: 36px;
          font-size: 14px;
          border-radius: 6px;
          min-width: 100px;
          padding: 0 12px;
          white-space: nowrap;
          text-align: center;
          display: flex;
          align-items: center;
          justify-content: center;
          
          &.el-button--primary {
            background-color: #409eff;
            border-color: #409eff;
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
