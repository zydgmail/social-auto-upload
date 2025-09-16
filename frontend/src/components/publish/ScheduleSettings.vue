<template>
  <div class="schedule-section">
    <h3>定时发布</h3>
    <div class="schedule-controls">
      <el-switch
        v-model="scheduleEnabled"
        active-text="定时发布"
        inactive-text="立即发布"
        @change="handleScheduleChange"
      />
      <div v-if="scheduleEnabled" class="schedule-settings">
        <div class="schedule-item">
          <span class="label">每天发布视频数：</span>
          <el-select v-model="videosPerDay" placeholder="选择发布数量">
            <el-option
              v-for="num in 55"
              :key="num"
              :label="num"
              :value="num"
            />
          </el-select>
        </div>
        <div class="schedule-item">
          <span class="label">每天发布时间：</span>
          <div class="time-selectors">
            <el-time-select
              v-for="(time, index) in dailyTimes"
              :key="index"
              v-model="dailyTimes[index]"
              start="00:00"
              step="00:30"
              end="23:30"
              placeholder="选择时间"
            />
            <el-button
              v-if="dailyTimes.length < videosPerDay"
              type="primary"
              size="small"
              @click="addTimeSlot"
            >
              添加时间
            </el-button>
          </div>
        </div>
        <div class="schedule-item">
          <span class="label">开始天数：</span>
          <el-select v-model="startDays" placeholder="选择开始天数">
            <el-option :label="'明天'" :value="0" />
            <el-option :label="'后天'" :value="1" />
          </el-select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  scheduleEnabled: {
    type: Boolean,
    default: false
  },
  videosPerDay: {
    type: Number,
    default: 1
  },
  dailyTimes: {
    type: Array,
    default: () => ['10:00']
  },
  startDays: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:scheduleEnabled', 'update:videosPerDay', 'update:dailyTimes', 'update:startDays'])

const scheduleEnabled = computed({
  get: () => props.scheduleEnabled,
  set: (value) => emit('update:scheduleEnabled', value)
})

const videosPerDay = computed({
  get: () => props.videosPerDay,
  set: (value) => emit('update:videosPerDay', value)
})

const dailyTimes = computed({
  get: () => props.dailyTimes,
  set: (value) => emit('update:dailyTimes', value)
})

const startDays = computed({
  get: () => props.startDays,
  set: (value) => emit('update:startDays', value)
})

const handleScheduleChange = (value) => {
  if (!value) {
    // 关闭定时发布时，重置为默认值
    emit('update:videosPerDay', 1)
    emit('update:dailyTimes', ['10:00'])
    emit('update:startDays', 0)
  }
}

const addTimeSlot = () => {
  if (dailyTimes.value.length < videosPerDay.value) {
    const newTimes = [...dailyTimes.value, '10:00']
    emit('update:dailyTimes', newTimes)
  }
}
</script>

<style lang="scss" scoped>
.schedule-section {
  margin-bottom: 30px;
  
  h3 {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
    margin: 0 0 10px 0;
  }
  
  .schedule-controls {
    display: flex;
    flex-direction: column;
    gap: 15px;

    .schedule-settings {
      margin-top: 15px;
      padding: 15px;
      background-color: #f5f7fa;
      border-radius: 4px;

      .schedule-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 15px;

        &:last-child {
          margin-bottom: 0;
        }

        .label {
          min-width: 120px;
          margin-right: 10px;
          line-height: 32px;
        }

        .time-selectors {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          align-items: center;
          
          .el-time-select {
            margin-right: 10px;
          }

          .el-button {
            margin-left: 10px;
          }
        }
      }
    }
  }
}
</style>
