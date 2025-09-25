<template>
  <div class="common-form">
    <!-- 标题输入 -->
    <TitleInput
      v-model="title"
      :platform-key="platformKey"
      @validation-change="(validation) => $emit('validation-change', 'title', validation)"
    />

    <!-- 话题输入 -->
    <TopicInput
      v-model="topics"
      :platform-key="platformKey"
      @validation-change="(validation) => $emit('validation-change', 'topics', validation)"
    />

    <!-- 通用说明 -->
    <div class="common-notice">
      <el-alert
        title="通用表单"
        description="当前平台使用通用表单模板，如需平台专属字段，请联系开发者添加。"
        type="info"
        :closable="false"
        show-icon
      />
    </div>
  </div>
</template>

<script setup>
import TitleInput from '../TitleInput.vue'
import TopicInput from '../TopicInput.vue'

// 定义props
defineProps({
  platformKey: {
    type: Number,
    required: true
  }
})

// 定义模型
const title = defineModel('title', { type: String, default: '' })
const topics = defineModel('topics', { type: Array, default: () => [] })

// 定义事件
defineEmits(['validation-change'])
</script>

<style scoped>
.common-form {
  margin-bottom: 20px;
}

.common-notice {
  margin-top: 16px;
}
</style>
