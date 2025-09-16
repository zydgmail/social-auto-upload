<template>
  <div class="account-section">
    <h3>账号</h3>
    <div class="account-display">
      <div class="selected-accounts">
        <el-tag
          v-for="(account, index) in selectedAccounts"
          :key="index"
          closable
          @close="removeAccount(index)"
          class="account-tag"
        >
          {{ getAccountDisplayName(account) }}
        </el-tag>
      </div>
      <el-button 
        type="primary" 
        plain 
        @click="openAccountDialog"
        class="select-account-btn"
      >
        选择账号
      </el-button>
    </div>

    <!-- 账号选择弹窗 -->
    <el-dialog
      v-model="accountDialogVisible"
      title="选择账号"
      width="600px"
      class="account-dialog"
    >
      <div class="account-dialog-content">
        <el-checkbox-group v-model="tempSelectedAccounts">
          <div class="account-list">
            <el-checkbox
              v-for="account in availableAccounts"
              :key="account.id"
              :label="account.id"
              class="account-item"
            >
              <div class="account-info">
                <span class="account-name">{{ account.name }}</span>                      
              </div>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="accountDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAccountSelection">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAccountStore } from '@/stores/account'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  platformKey: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const accountStore = useAccountStore()

const selectedAccounts = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 弹窗状态
const accountDialogVisible = ref(false)
const tempSelectedAccounts = ref([])

// 根据选择的平台获取可用账号列表
const availableAccounts = computed(() => {
  const platformMap = {
    3: '抖音',
    2: '视频号',
    1: '小红书',
    4: '快手'
  }
  const currentPlatform = platformMap[props.platformKey]
  return currentPlatform ? accountStore.accounts.filter(acc => acc.platform === currentPlatform) : []
})

// 打开账号选择弹窗
const openAccountDialog = () => {
  tempSelectedAccounts.value = [...selectedAccounts.value]
  accountDialogVisible.value = true
}

// 确认账号选择
const confirmAccountSelection = () => {
  selectedAccounts.value = [...tempSelectedAccounts.value]
  accountDialogVisible.value = false
  ElMessage.success('账号选择完成')
}

// 删除选中的账号
const removeAccount = (index) => {
  selectedAccounts.value.splice(index, 1)
}

// 获取账号显示名称
const getAccountDisplayName = (accountId) => {
  const account = accountStore.accounts.find(acc => acc.id === accountId)
  return account ? account.name : accountId
}
</script>

<style lang="scss" scoped>
.account-section {
  margin-bottom: 30px;
  
  h3 {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin: 0 0 10px 0;
  }
  
  .account-display {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .selected-accounts {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      min-height: 32px;
      
      .account-tag {
        font-size: 14px;
      }
    }
    
    .select-account-btn {
      align-self: flex-start;
    }
  }
  
  .account-dialog-content {
    max-height: 400px;
    overflow-y: auto;
    
    .account-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .account-item {
        width: 100%;
        
        .account-info {
          display: flex;
          align-items: center;
          
          .account-name {
            font-weight: 500;
            color: #303133;
          }
        }
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}
</style>
