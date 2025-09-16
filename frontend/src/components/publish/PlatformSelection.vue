<template>
  <div class="platform-section">
    <h3>平台</h3>
    <el-radio-group v-model="selectedPlatform" @change="handlePlatformChange" class="platform-radios">
      <el-radio 
        v-for="platform in platforms" 
        :key="platform.key"
        :label="platform.key"
        class="platform-radio"
      >
        {{ platform.name }}
      </el-radio>
    </el-radio-group>
    
    <!-- 平台配置提示 -->
    <div v-if="currentConfig" class="platform-tips">
      <el-alert
        :title="`${currentConfig.name}平台限制：标题最多${currentConfig.titleLimit}字，话题最多${currentConfig.topicLimit}个`"
        type="info"
        :closable="false"
        show-icon
        class="platform-alert"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getAllPlatforms, getPlatformConfig } from '@/utils/platformConfig'

const props = defineProps({
  modelValue: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'platform-change'])

const platforms = getAllPlatforms()

const selectedPlatform = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const currentConfig = computed(() => {
  return getPlatformConfig(props.modelValue)
})

const handlePlatformChange = (value) => {
  emit('platform-change', value)
}
</script>

<style lang="scss" scoped>
.platform-section {
  margin-bottom: 30px;
  
  h3 {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin: 0 0 10px 0;
  }
  
  .platform-radios {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin-bottom: 15px;
    
    .platform-radio {
      font-size: 14px;
    }
  }
  
  .platform-tips {
    .platform-alert {
      font-size: 13px;
    }
  }
}
</style>
