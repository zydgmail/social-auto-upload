<template>
  <div class="upload-section">
    <h3>视频</h3>
    <div class="upload-options">
      <el-button type="primary" @click="showUploadOptions" class="upload-btn">
        <el-icon><Upload /></el-icon>
        上传视频
      </el-button>
    </div>
    
    <!-- 已上传文件列表 -->
    <div v-if="fileList.length > 0" class="uploaded-files">
      <h4>已上传文件：</h4>
      <div class="file-list">
        <div v-for="(file, index) in fileList" :key="index" class="file-item">
          <el-link :href="file.url" target="_blank" type="primary">{{ file.name }}</el-link>
          <span class="file-size">{{ (file.size / 1024 / 1024).toFixed(2) }}MB</span>
          <el-button type="danger" size="small" @click="$emit('remove-file', index)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- 上传选项弹窗 -->
    <el-dialog
      v-model="uploadOptionsVisible"
      title="选择上传方式"
      width="400px"
      class="upload-options-dialog"
    >
      <div class="upload-options-content">
        <el-button type="primary" @click="selectLocalUpload" class="option-btn">
          <el-icon><Upload /></el-icon>
          本地上传
        </el-button>
        <el-button type="success" @click="selectMaterialLibrary" class="option-btn">
          <el-icon><Folder /></el-icon>
          素材库
        </el-button>
      </div>
    </el-dialog>

    <!-- 本地上传弹窗 -->
    <el-dialog
      v-model="localUploadVisible"
      title="本地上传"
      width="600px"
      class="local-upload-dialog"
    >
      <el-upload
        class="video-upload"
        drag
        :auto-upload="true"
        :action="uploadAction"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        multiple
        accept="video/*"
        :headers="authHeaders"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          将视频文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持MP4、AVI等视频格式，可上传多个文件
          </div>
        </template>
      </el-upload>
    </el-dialog>

    <!-- 素材库选择弹窗 -->
    <el-dialog
      v-model="materialLibraryVisible"
      title="选择素材"
      width="800px"
      class="material-library-dialog"
    >
      <div class="material-library-content">
        <el-checkbox-group v-model="selectedMaterials">
          <div class="material-list">
            <div
              v-for="material in materials"
              :key="material.id"
              class="material-item"
            >
              <el-checkbox :label="material.id" class="material-checkbox">
                <div class="material-info">
                  <div class="material-name">{{ material.filename }}</div>
                  <div class="material-details">
                    <span class="file-size">{{ material.filesize }}MB</span>
                    <span class="upload-time">{{ material.upload_time }}</span>
                  </div>
                </div>
              </el-checkbox>
            </div>
          </div>
        </el-checkbox-group>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="materialLibraryVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmMaterialSelection">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Upload, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { materialApi } from '@/api/material'

const props = defineProps({
  fileList: {
    type: Array,
    default: () => []
  },
  uploadAction: {
    type: String,
    required: true
  },
  authHeaders: {
    type: Object,
    required: true
  },
  materials: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['show-upload-options', 'remove-file', 'upload-success', 'material-selected'])

const appStore = useAppStore()

// 弹窗状态
const uploadOptionsVisible = ref(false)
const localUploadVisible = ref(false)
const materialLibraryVisible = ref(false)
const selectedMaterials = ref([])

// 选择本地上传
const selectLocalUpload = () => {
  uploadOptionsVisible.value = false
  localUploadVisible.value = true
}

// 选择素材库
const selectMaterialLibrary = async () => {
  uploadOptionsVisible.value = false
  
  // 如果素材库为空，先获取素材数据
  if (props.materials.length === 0) {
    try {
      const response = await materialApi.getAllMaterials()
      if (response.code === 200) {
        appStore.setMaterials(response.data)
      } else {
        ElMessage.error('获取素材列表失败')
        return
      }
    } catch (error) {
      console.error('获取素材列表出错:', error)
      ElMessage.error('获取素材列表失败')
      return
    }
  }
  
  selectedMaterials.value = []
  materialLibraryVisible.value = true
}

// 处理文件上传成功
const handleUploadSuccess = (response, file) => {
  if (response.code === 200) {
    emit('upload-success', response, file)
    localUploadVisible.value = false
    ElMessage.success('文件上传成功')
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}

// 处理文件上传失败
const handleUploadError = (error) => {
  ElMessage.error('文件上传失败')
  console.error('上传错误:', error)
}

// 确认素材选择
const confirmMaterialSelection = () => {
  if (selectedMaterials.value.length === 0) {
    ElMessage.warning('请选择至少一个素材')
    return
  }
  
  emit('material-selected', selectedMaterials.value)
  
  const addedCount = selectedMaterials.value.length
  materialLibraryVisible.value = false
  selectedMaterials.value = []
  ElMessage.success(`已添加 ${addedCount} 个素材`)
}

// 显示上传选项
const showUploadOptions = () => {
  uploadOptionsVisible.value = true
}

// 暴露方法给父组件
defineExpose({
  showUploadOptions
})
</script>

<style lang="scss" scoped>
.upload-section {
  margin-bottom: 30px;
  
  h3 {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin: 0 0 10px 0;
  }
  
  .upload-options {
    margin-bottom: 20px;
  }
  
  .video-upload {
    width: 100%;
    
    :deep(.el-upload-dragger) {
      width: 100%;
      height: 180px;
    }
  }
  
  .upload-options-content {
    display: flex;
    flex-direction: column;
    gap: 15px;
    
    .option-btn {
      width: 100%;
      height: 50px;
      font-size: 16px;
      margin: 0 !important; // 重置所有margin
    }
  }
  
  .material-library-content {
    max-height: 400px;
    overflow-y: auto;
    
    .material-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .material-item {
        .material-checkbox {
          width: 100%;
          
          .material-info {
            display: flex;
            flex-direction: column;
            gap: 5px;
            
            .material-name {
              font-weight: 500;
              color: #303133;
            }
            
            .material-details {
              display: flex;
              gap: 15px;
              font-size: 12px;
              color: #909399;
            }
          }
        }
      }
    }
  }
  
  .uploaded-files {
    margin-top: 20px;
    
    h4 {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 12px;
      color: #303133;
    }
    
    .file-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .file-item {
        display: flex;
        align-items: center;
        padding: 10px 15px;
        background-color: #f5f7fa;
        border-radius: 4px;
        
        .el-link {
          margin-right: 10px;
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .file-size {
          color: #909399;
          font-size: 13px;
          margin-right: auto;
        }
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}
</style>
