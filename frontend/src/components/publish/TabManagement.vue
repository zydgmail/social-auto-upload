<template>
  <div class="tab-management">
    <div class="tab-header">
      <div class="tab-list">
        <div 
          v-for="tab in tabs" 
          :key="tab.name"
          :class="['tab-item', { active: activeTab === tab.name }]"
          @click="$emit('tab-change', tab.name)"
        >
          <span>{{ tab.label }}</span>
          <el-icon 
            v-if="tabs.length > 1"
            class="close-icon" 
            @click.stop="$emit('remove-tab', tab.name)"
          >
            <Close />
          </el-icon>
        </div>
      </div>
      <div class="tab-actions">
        <el-button 
          type="primary" 
          size="small" 
          @click="$emit('add-tab')"
          class="add-tab-btn"
        >
          <el-icon><Plus /></el-icon>
          添加Tab
        </el-button>
        <el-button 
          type="success" 
          size="small" 
          @click="$emit('batch-publish')"
          :loading="batchPublishing"
          class="batch-publish-btn"
        >
          批量发布
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, Close } from '@element-plus/icons-vue'

defineProps({
  tabs: {
    type: Array,
    required: true
  },
  activeTab: {
    type: String,
    required: true
  },
  batchPublishing: {
    type: Boolean,
    default: false
  }
})

defineEmits(['tab-change', 'remove-tab', 'add-tab', 'batch-publish'])
</script>

<style lang="scss" scoped>
.tab-management {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 15px 20px;
  
  .tab-header {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    
    .tab-list {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      flex: 1;
      min-width: 0;
      
      .tab-item {
         display: flex;
         align-items: center;
         gap: 6px;
         padding: 6px 12px;
         background-color: #f5f7fa;
         border: 1px solid #dcdfe6;
         border-radius: 4px;
         cursor: pointer;
         transition: all 0.3s;
         font-size: 14px;
         height: 32px;
         
         &:hover {
           background-color: #ecf5ff;
           border-color: #b3d8ff;
         }
         
         &.active {
           background-color: #409eff;
           border-color: #409eff;
           color: #fff;
           
           .close-icon {
             color: #fff;
             
             &:hover {
               background-color: rgba(255, 255, 255, 0.2);
             }
           }
         }
         
         .close-icon {
           padding: 2px;
           border-radius: 2px;
           cursor: pointer;
           transition: background-color 0.3s;
           font-size: 12px;
           
           &:hover {
             background-color: rgba(0, 0, 0, 0.1);
           }
         }
       }
     }
     
    .tab-actions {
      display: flex;
      gap: 10px;
      flex-shrink: 0;
      
      .add-tab-btn,
      .batch-publish-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        height: 32px;
        padding: 6px 12px;
        font-size: 14px;
        white-space: nowrap;
      }
    }
  }
}
</style>
