<template>
  <div class="bilibili-form">
    <!-- B站专属字段 -->
    <div class="bili-specific-fields">
      <el-form label-width="90px">
        <!-- 标题输入 -->
        <el-form-item label="标题" required>
          <el-input
            v-model="title"
            placeholder="请输入稿件标题"
            maxlength="80"
            show-word-limit
            clearable
          />
          <div class="field-tips">
            <el-text size="small" type="info">好的标题有助于作品获得更多推荐</el-text>
          </div>
        </el-form-item>

        <!-- 类型选择 -->
        <el-form-item label="类型" required>
          <el-radio-group v-model="biliType">
            <el-radio label="自制">自制</el-radio>
            <el-radio label="转载">转载</el-radio>
          </el-radio-group>
          <div class="field-tips">
            <el-text size="small" type="info">自制=原创内容，转载=搬运内容</el-text>
          </div>
        </el-form-item>

        <!-- 分区选择 - 基于B站上传页面实际分区 -->
        <el-form-item label="分区" required>
          <el-select 
            v-model="biliPartition" 
            placeholder="请选择分区"
            filterable
            clearable
            style="width: 100%"
          >
            <!-- 请访问 https://member.bilibili.com/platform/upload/video/frame 获取实际分区选项 -->
            <!-- 以下为从上传页抓取到的一级分区选项（无二级） -->
            <el-option label="影视" value="影视" />
            <el-option label="娱乐" value="娱乐" />
            <el-option label="音乐" value="音乐" />
            <el-option label="舞蹈" value="舞蹈" />
            <el-option label="动画" value="动画" />
            <el-option label="绘画" value="绘画" />
            <el-option label="鬼畜" value="鬼畜" />
            <el-option label="游戏" value="游戏" />
            <el-option label="资讯" value="资讯" />
            <el-option label="知识" value="知识" />
            <el-option label="人工智能" value="人工智能" />
            <el-option label="科技数码" value="科技数码" />
            <el-option label="汽车" value="汽车" />
            <el-option label="时尚美妆" value="时尚美妆" />
            <el-option label="家装房产" value="家装房产" />
            <el-option label="户外潮流" value="户外潮流" />
            <el-option label="健身" value="健身" />
            <el-option label="体育运动" value="体育运动" />
            <el-option label="手工" value="手工" />
            <el-option label="美食" value="美食" />
            <el-option label="小剧场" value="小剧场" />
            <el-option label="旅游出行" value="旅游出行" />
            <el-option label="三农" value="三农" />
            <el-option label="动物" value="动物" />
            <el-option label="亲子" value="亲子" />
            <el-option label="健康" value="健康" />
            <el-option label="情感" value="情感" />
            <el-option label="vlog" value="vlog" />
            <el-option label="生活兴趣" value="生活兴趣" />
            <el-option label="生活经验" value="生活经验" />
          </el-select>
          <div class="field-tips">
            <el-text size="small" type="warning">
              ⚠️ 分区选项需要根据B站实际页面更新。请访问 
              <a href="https://member.bilibili.com/platform/upload/video/frame" target="_blank" style="color: #409eff;">
                B站上传页面
              </a> 
              查看实际分区列表。
            </el-text>
          </div>
        </el-form-item>

                   <!-- 标签输入 -->
                   <el-form-item label="标签" required>
                     <BiliTagInput
                       v-model="topics"
                       @validation-change="(validation) => $emit('validation-change', 'topics', validation)"
                     />
                   </el-form-item>

        <!-- 简介输入 -->
        <el-form-item label="简介">
          <el-input
            v-model="biliDesc"
            type="textarea"
            :rows="5"
            maxlength="2000"
            show-word-limit
            placeholder="填写更全面的相关信息，让更多的人能够找到你的视频吧"
            resize="vertical"
          />
          <div class="field-tips">
            <el-text size="small" type="info">简介支持@用户、#话题、超链接</el-text>
          </div>
        </el-form-item>

        <!-- 定时发布 -->
        <el-form-item label="定时发布">
          <div class="schedule-setting">
            <el-switch 
              v-model="scheduleEnabled" 
              active-text="启用定时发布"
              inactive-text="立即发布"
            />
            <div v-if="scheduleEnabled" class="schedule-datetime">
              <el-date-picker
                v-model="scheduleTime"
                type="datetime"
                placeholder="选择发布时间"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm"
                :disabled-date="disabledDate"
                :disabled-hours="disabledHours"
                :disabled-minutes="disabledMinutes"
                style="width: 100%; margin-top: 8px;"
              />
            </div>
          </div>
          <div class="field-tips">
            <el-text size="small" type="info">可设置未来7天内的发布时间</el-text>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BiliTagInput from './BiliTagInput.vue'

// 定义模型
const title = defineModel('title', { type: String, default: '' })
const topics = defineModel('topics', { type: Array, default: () => [] })
const biliType = defineModel('biliType', { type: String, default: '自制' })
const biliPartition = defineModel('biliPartition', { type: String, default: '' })
const biliDesc = defineModel('biliDesc', { type: String, default: '' })
const scheduleEnabled = defineModel('scheduleEnabled', { type: Boolean, default: false })
const scheduleTime = defineModel('scheduleTime', { type: String, default: '' })

// 定义事件
defineEmits(['validation-change'])

// 定时发布日期时间限制
const disabledDate = (time) => {
  const now = new Date()
  const sevenDaysLater = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
  return time.getTime() < now.getTime() || time.getTime() > sevenDaysLater.getTime()
}

const disabledHours = () => {
  const now = new Date()
  const selectedDate = new Date(scheduleTime.value)
  if (selectedDate.toDateString() === now.toDateString()) {
    // 如果是今天，禁用已过去的小时
    return Array.from({ length: now.getHours() }, (_, i) => i)
  }
  return []
}

const disabledMinutes = (hour) => {
  const now = new Date()
  const selectedDate = new Date(scheduleTime.value)
  if (selectedDate.toDateString() === now.toDateString() && hour === now.getHours()) {
    // 如果是今天的当前小时，禁用已过去的分钟
    return Array.from({ length: now.getMinutes() }, (_, i) => i)
  }
  return []
}
</script>

<style scoped>
.bilibili-form {
  margin-bottom: 20px;
}

.bili-specific-fields {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.field-tips {
  margin-top: 4px;
}

.field-tips .el-text {
  color: #909399;
}

.schedule-setting {
  width: 100%;
}

.schedule-datetime {
  margin-top: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

:deep(.el-radio-group) {
  width: 100%;
}

:deep(.el-radio) {
  margin-right: 24px;
}

:deep(.el-select .el-input__wrapper) {
  min-height: 36px;
}

:deep(.el-textarea .el-textarea__inner) {
  min-height: 120px;
  resize: vertical;
}

:deep(.el-switch) {
  height: 22px;
}

:deep(.el-switch__label) {
  font-size: 14px;
  color: #606266;
}

:deep(.el-date-editor) {
  width: 100%;
}

/* 分区选择器样式优化 */
:deep(.el-select-dropdown__item) {
  padding: 8px 12px;
}

:deep(.el-select-group__title) {
  padding: 8px 12px;
  font-weight: 600;
  color: #409eff;
  background-color: #f0f9ff;
}

/* 标签选择器样式 */
:deep(.el-select .el-select__tags) {
  max-width: 100%;
}

:deep(.el-tag) {
  margin: 2px;
  background-color: #409eff;
  color: white;
  border-color: #409eff;
}
</style>
