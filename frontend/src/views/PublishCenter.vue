<template>
  <div class="publish-center">
    <!-- Tab管理区域 -->
    <TabManagement
      :tabs="tabs"
      :active-tab="activeTab"
      :batch-publishing="batchPublishing"
      @tab-change="activeTab = $event"
      @remove-tab="removeTab"
      @add-tab="addTab"
      @batch-publish="batchPublish"
    />

    <!-- 内容区域 -->
    <div class="publish-content">
      <div class="tab-content-wrapper">
        <div 
          v-for="tab in tabs" 
          :key="tab.name"
          v-show="activeTab === tab.name"
          class="tab-content"
        >
          <!-- 发布状态提示 -->
          <div v-if="tab.publishStatus" class="publish-status">
            <el-alert
              :title="tab.publishStatus.message"
              :type="tab.publishStatus.type"
              :closable="false"
              show-icon
            />
          </div>

          <!-- 视频上传区域 -->
          <VideoUpload
            :file-list="tab.fileList"
            :upload-action="`${apiBaseUrl}/upload`"
            :auth-headers="authHeaders"
            :materials="materials"
            @remove-file="(index) => removeFile(tab, index)"
            @upload-success="(response, file) => handleUploadSuccess(response, file, tab)"
            @material-selected="(materials) => handleMaterialSelected(materials, tab)"
          />

          <!-- 平台选择 -->
          <PlatformSelection
            v-model="tab.selectedPlatform"
            @platform-change="handlePlatformChange"
          />

          <!-- 账号选择 -->
          <AccountSelection
            v-model="tab.selectedAccounts"
            :platform-key="tab.selectedPlatform"
          />

          <!-- 标题输入 -->
          <TitleInput
            v-model="tab.title"
            :platform-key="tab.selectedPlatform"
            @validation-change="(validation) => handleValidationChange('title', validation, tab)"
          />

          <!-- 话题输入 -->
          <TopicInput
            v-model="tab.selectedTopics"
            :platform-key="tab.selectedPlatform"
            @validation-change="(validation) => handleValidationChange('topics', validation, tab)"
          />

          <!-- 定时发布 -->
          <ScheduleSettings
            v-model:schedule-enabled="tab.scheduleEnabled"
            v-model:videos-per-day="tab.videosPerDay"
            v-model:daily-times="tab.dailyTimes"
            v-model:start-days="tab.startDays"
          />

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button size="small" @click="cancelPublish(tab)">取消</el-button>
            <el-button size="small" type="primary" @click="confirmPublish(tab)">发布</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量发布进度对话框 -->
    <el-dialog
      v-model="batchPublishDialogVisible"
      title="批量发布进度"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="publish-progress">
        <el-progress 
          :percentage="publishProgress"
          :status="publishProgress === 100 ? 'success' : ''"
        />
        <div v-if="currentPublishingTab" class="current-publishing">
          正在发布：{{ currentPublishingTab.label }}
        </div>
        
        <!-- 发布结果列表 -->
        <div class="publish-results" v-if="publishResults.length > 0">
          <div 
            v-for="(result, index) in publishResults" 
            :key="index"
            :class="['result-item', result.status]"
          >
            <el-icon v-if="result.status === 'success'"><Check /></el-icon>
            <el-icon v-else-if="result.status === 'error'"><Close /></el-icon>
            <el-icon v-else><InfoFilled /></el-icon>
            <span class="label">{{ result.label }}</span>
            <span class="message">{{ result.message }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button 
            @click="cancelBatchPublish" 
            :disabled="publishProgress === 100"
          >
            取消发布
          </el-button>
          <el-button 
            type="primary" 
            @click="batchPublishDialogVisible = false"
            v-if="publishProgress === 100"
          >
            关闭
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { Check, Close, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { materialApi } from '@/api/material'
import { validatePublishForm } from '@/utils/formValidation'

// 导入子组件
import TabManagement from '@/components/publish/TabManagement.vue'
import VideoUpload from '@/components/publish/VideoUpload.vue'
import PlatformSelection from '@/components/publish/PlatformSelection.vue'
import AccountSelection from '@/components/publish/AccountSelection.vue'
import TitleInput from '@/components/publish/TitleInput.vue'
import TopicInput from '@/components/publish/TopicInput.vue'
import ScheduleSettings from '@/components/publish/ScheduleSettings.vue'

// API base URL
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

// Authorization headers
const authHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
}))

// 当前激活的tab
const activeTab = ref('tab1')

// tab计数器
let tabCounter = 1

// 获取应用状态管理
const appStore = useAppStore()
const accountStore = useAccountStore()

// 素材数据
const materials = computed(() => appStore.materials)

// 批量发布相关状态
const batchPublishing = ref(false)

// tab页数据 - 默认只有一个tab
const tabs = reactive([
  {
    name: 'tab1',
    label: '发布1',
    fileList: [], // 后端返回的文件名列表
    displayFileList: [], // 用于显示的文件列表
    selectedAccounts: [], // 选中的账号ID列表
    selectedPlatform: 1, // 选中的平台（单选）
    title: '',
    selectedTopics: [], // 话题列表（不带#号）
    scheduleEnabled: false, // 定时发布开关
    videosPerDay: 1, // 每天发布视频数量
    dailyTimes: ['10:00'], // 每天发布时间点列表
    startDays: 0, // 从今天开始计算的发布天数，0表示明天，1表示后天
    publishStatus: null, // 发布状态，包含message和type
    validationErrors: {} // 验证错误信息
  }
])

// 批量发布对话框状态
const batchPublishDialogVisible = ref(false)
const currentPublishingTab = ref(null)
const publishProgress = ref(0)
const publishResults = ref([])
const isCancelled = ref(false)

// 添加新tab
const addTab = () => {
  tabCounter++
  const newTab = {
    name: `tab${tabCounter}`,
    label: `发布${tabCounter}`,
    fileList: [],
    displayFileList: [],
    selectedAccounts: [],
    selectedPlatform: 1,
    title: '',
    selectedTopics: [],
    scheduleEnabled: false,
    videosPerDay: 1,
    dailyTimes: ['10:00'],
    startDays: 0,
    publishStatus: null,
    validationErrors: {}
  }
  tabs.push(newTab)
  activeTab.value = newTab.name
}

// 删除tab
const removeTab = (tabName) => {
  const index = tabs.findIndex(tab => tab.name === tabName)
  if (index > -1) {
    tabs.splice(index, 1)
    // 如果删除的是当前激活的tab，切换到第一个tab
    if (activeTab.value === tabName && tabs.length > 0) {
      activeTab.value = tabs[0].name
    }
  }
}

// 处理平台变化
const handlePlatformChange = (platformKey) => {
  // 平台变化时，清空账号选择
  const currentTab = tabs.find(tab => tab.name === activeTab.value)
  if (currentTab) {
    currentTab.selectedAccounts = []
  }
}

// 处理验证变化
const handleValidationChange = (fieldName, validation, tab) => {
  if (validation.valid) {
    delete tab.validationErrors[fieldName]
  } else {
    tab.validationErrors[fieldName] = validation.message
  }
}

// 处理文件上传成功
const handleUploadSuccess = (response, file, tab) => {
  if (response.code === 200) {
    // 获取文件路径
    const filePath = response.data.path || response.data
    // 从路径中提取文件名
    const filename = filePath.split('/').pop()
    
    // 保存文件信息到fileList，包含文件路径和其他信息
    const fileInfo = {
      name: file.name,
      url: materialApi.getMaterialPreviewUrl(filename), // 使用getMaterialPreviewUrl生成预览URL
      path: filePath,
      size: file.size,
      type: file.type
    }
    
    // 添加到文件列表
    tab.fileList.push(fileInfo)
    
    // 更新显示列表
    tab.displayFileList = [...tab.fileList.map(item => ({
      name: item.name,
      url: item.url
    }))]
    
    ElMessage.success('文件上传成功')
    console.log('上传成功:', fileInfo)
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}

// 处理素材选择
const handleMaterialSelected = (selectedMaterials, tab) => {
  selectedMaterials.forEach(materialId => {
    const material = materials.value.find(m => m.id === materialId)
    if (material) {
      const fileInfo = {
        name: material.filename,
        url: materialApi.getMaterialPreviewUrl(material.file_path.split('/').pop()),
        path: material.file_path,
        size: material.filesize * 1024 * 1024, // 转换为字节
        type: 'video/mp4'
      }
      
      // 检查是否已存在相同文件
      const exists = tab.fileList.some(file => file.path === fileInfo.path)
      if (!exists) {
        tab.fileList.push(fileInfo)
      }
    }
  })
  
  // 更新显示列表
  tab.displayFileList = [...tab.fileList.map(item => ({
    name: item.name,
    url: item.url
  }))]
}

// 删除已上传文件
const removeFile = (tab, index) => {
  // 从文件列表中删除
  tab.fileList.splice(index, 1)
  
  // 更新显示列表
  tab.displayFileList = [...tab.fileList.map(item => ({
    name: item.name,
    url: item.url
  }))]
  
  ElMessage.success('文件删除成功')
}

// 取消发布
const cancelPublish = (tab) => {
  ElMessage.info('已取消发布')
}

// 确认发布
const confirmPublish = async (tab) => {
  return new Promise((resolve, reject) => {
    // 使用新的验证函数
    const validation = validatePublishForm(tab)
    if (!validation.valid) {
      const firstError = Object.values(validation.errors)[0]
      ElMessage.error(firstError)
      reject(new Error(firstError))
      return
    }
    
    // 构造发布数据，符合后端API格式
    const publishData = {
      type: tab.selectedPlatform,
      title: tab.title,
      tags: tab.selectedTopics, // 不带#号的话题列表
      fileList: tab.fileList.map(file => file.path), // 只发送文件路径
      accountList: tab.selectedAccounts.map(accountId => {
        const account = accountStore.accounts.find(acc => acc.id === accountId)
        return account ? account.filePath : accountId
      }), // 发送账号的文件路径
      enableTimer: tab.scheduleEnabled ? 1 : 0, // 是否启用定时发布，开启传1，不开启传0
      videosPerDay: tab.scheduleEnabled ? tab.videosPerDay || 1 : 1, // 每天发布视频数量，1-55
      dailyTimes: tab.scheduleEnabled ? tab.dailyTimes || ['10:00'] : ['10:00'], // 每天发布时间点
      startDays: tab.scheduleEnabled ? tab.startDays || 0 : 0, // 从今天开始计算的发布天数，0表示明天，1表示后天
      category: 0 //表示非原创
    }
    
    // 调用后端发布API
    fetch(`${apiBaseUrl}/postVideo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders.value
      },
      body: JSON.stringify(publishData)
    })
    .then(response => response.json())
    .then(data => {
      if (data.code === 200) {
        tab.publishStatus = {
          message: '发布成功',
          type: 'success'
        }
        // 清空当前tab的数据
        tab.fileList = []
        tab.displayFileList = []
        tab.title = ''
        tab.selectedTopics = []
        tab.selectedAccounts = []
        tab.scheduleEnabled = false
        tab.validationErrors = {}
        resolve()
      } else {
        tab.publishStatus = {
          message: `发布失败：${data.msg || '发布失败'}`,
          type: 'error'
        }
        reject(new Error(data.msg || '发布失败'))
      }
    })
    .catch(error => {
      console.error('发布错误:', error)
      tab.publishStatus = {
        message: '发布失败，请检查网络连接',
        type: 'error'
      }
      reject(error)
    })
  })
}

// 批量发布方法
const batchPublish = async () => {
  if (batchPublishing.value) return
  
  batchPublishing.value = true
  currentPublishingTab.value = null
  publishProgress.value = 0
  publishResults.value = []
  isCancelled.value = false
  batchPublishDialogVisible.value = true
  
  try {
    for (let i = 0; i < tabs.length; i++) {
      if (isCancelled.value) {
        publishResults.value.push({
          label: tabs[i].label,
          status: 'cancelled',
          message: '已取消'
        })
        continue
      }

      const tab = tabs[i]
      currentPublishingTab.value = tab
      publishProgress.value = Math.floor((i / tabs.length) * 100)
      
      try {
        await confirmPublish(tab)
        publishResults.value.push({
          label: tab.label,
          status: 'success',
          message: '发布成功'
        })
      } catch (error) {
        publishResults.value.push({
          label: tab.label,
          status: 'error',
          message: error.message
        })
        // 不立即返回，继续显示发布结果
      }
    }
    
    publishProgress.value = 100
    
    // 统计发布结果
    const successCount = publishResults.value.filter(r => r.status === 'success').length
    const failCount = publishResults.value.filter(r => r.status === 'error').length
    const cancelCount = publishResults.value.filter(r => r.status === 'cancelled').length
    
    if (isCancelled.value) {
      ElMessage.warning(`发布已取消：${successCount}个成功，${failCount}个失败，${cancelCount}个未执行`)
    } else if (failCount > 0) {
      ElMessage.error(`发布完成：${successCount}个成功，${failCount}个失败`)
    } else {
      ElMessage.success('所有Tab发布成功')
      setTimeout(() => {
        batchPublishDialogVisible.value = false
      }, 1000)
    }
    
  } catch (error) {
    console.error('批量发布出错:', error)
    ElMessage.error('批量发布出错，请重试')
  } finally {
    batchPublishing.value = false
    isCancelled.value = false
  }
}

// 取消批量发布
const cancelBatchPublish = () => {
  isCancelled.value = true
  ElMessage.info('正在取消发布...')
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.publish-center {
  display: flex;
  flex-direction: column;
  height: 100%;
  
  // 内容区域
  .publish-content {
    flex: 1;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 20px;
    
    .tab-content-wrapper {
      display: flex;
      justify-content: center;
      
      .tab-content {
        width: 100%;
        max-width: 800px;
        
        .publish-status {
          margin-bottom: 20px;
        }
        
        .action-buttons {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid #ebeef5;
        }
      }
    }
  }
  
  // 批量发布进度对话框样式
  .publish-progress {
    padding: 20px;
    
    .current-publishing {
      margin: 15px 0;
      text-align: center;
      color: #606266;
    }

    .publish-results {
      margin-top: 20px;
      border-top: 1px solid #EBEEF5;
      padding-top: 15px;
      max-height: 300px;
      overflow-y: auto;

      .result-item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        color: #606266;

        .el-icon {
          margin-right: 8px;
        }

        .label {
          margin-right: 10px;
          font-weight: 500;
        }

        .message {
          color: #909399;
        }

        &.success {
          color: #67C23A;
        }

        &.error {
          color: #F56C6C;
        }

        &.cancelled {
          color: #909399;
        }
      }
    }
  }

  .dialog-footer {
    text-align: right;
  }
}
</style>
