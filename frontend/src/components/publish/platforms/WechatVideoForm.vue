<template>
  <div class="wechat-video-form">
    <!-- 标题输入 -->
    <TitleInput
      v-model="title"
      :platform-key="2"
      @validation-change="(validation) => $emit('validation-change', 'title', validation)"
    />

    <!-- 话题输入 -->
    <TopicInput
      v-model="topics"
      :platform-key="2"
      @validation-change="(validation) => $emit('validation-change', 'topics', validation)"
    />

    <!-- 视频号特色字段可以在这里添加，比如：原创声明、位置等 -->
    <!-- 暂时保持与原来一致，后续可扩展 -->
  </div>
</template>

<script setup>
import TitleInput from '../TitleInput.vue'
import TopicInput from '../TopicInput.vue'

// 定义模型和事件
const title = defineModel('title', { type: String, default: '' })
const topics = defineModel('topics', { type: Array, default: () => [] })

// 定义事件
defineEmits(['validation-change'])
</script>

<style scoped>
.wechat-video-form {
  margin-bottom: 20px;
}
</style>
