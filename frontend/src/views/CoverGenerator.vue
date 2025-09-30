<template>
  <div class="cover-generator">
    <div class="page-header">
      <h1>封面生成</h1>
    </div>

    <div class="panel">
      <el-form label-width="90px" class="controls">
        <el-form-item label="标题文本">
          <el-input
            v-model="title"
            type="textarea"
            :rows="3"
            placeholder="输入封面标题，支持换行"
          />
        </el-form-item>
        <el-form-item label="背景图片">
          <el-upload
            :auto-upload="false"
            accept="image/*"
            :show-file-list="false"
            :on-change="onBgChange"
          >
            <el-button>选择图片</el-button>
          </el-upload>
          <span v-if="bgName" class="file-name">{{ bgName }}</span>
        </el-form-item>
        <el-form-item label="画布尺寸">
          <div class="size-row">
            <el-input-number v-model="canvasWidth" :min="320" :max="4096" />
            <span class="x">×</span>
            <el-input-number v-model="canvasHeight" :min="320" :max="4096" />
          </div>
        </el-form-item>
        <el-form-item label="字体大小">
          <el-slider v-model="fontSize" :min="24" :max="200" :step="2" style="width: 240px;" />
        </el-form-item>
        <el-form-item label="主色">
          <el-color-picker v-model="fillColor" />
        </el-form-item>
        <el-form-item label="描边色">
          <el-color-picker v-model="strokeColor" />
        </el-form-item>
        <el-form-item label="描边宽度">
          <el-slider v-model="strokeWidth" :min="0" :max="30" :step="1" style="width: 240px;" />
        </el-form-item>
        <el-form-item label="每行字数">
          <el-input-number v-model="wrapWidth" :min="6" :max="32" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="render">生成预览</el-button>
          <el-button type="success" @click="download">下载PNG</el-button>
        </el-form-item>
      </el-form>

      <div class="preview">
        <canvas ref="canvasRef" :width="canvasWidth" :height="canvasHeight"></canvas>
      </div>
    </div>
  </div>
  
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const title = ref('示例标题：AI 自动化运营系统\n高点击封面生成')
const canvasWidth = ref(1280)
const canvasHeight = ref(720)
const fontSize = ref(100)
const fillColor = ref('#ff6f91')
const strokeColor = ref('#ffffff')
const strokeWidth = ref(12)
const wrapWidth = ref(12)

const canvasRef = ref(null)
const bgImage = ref(null)
const bgName = ref('')

function onBgChange(file) {
  const raw = file.raw || file
  if (!raw) return
  bgName.value = raw.name
  const reader = new FileReader()
  reader.onload = () => {
    const img = new Image()
    img.onload = () => {
      bgImage.value = img
      render()
    }
    img.src = reader.result
  }
  reader.readAsDataURL(raw)
}

function wrapText(text, width) {
  const words = text.replace(/\r/g, '').split(/\n|\s+/)
  const lines = []
  let current = ''
  for (const word of words) {
    if (word === '') continue
    if ((current + (current ? ' ' : '') + word).length <= width) {
      current = current ? current + ' ' + word : word
    } else {
      if (current) lines.push(current)
      current = word
    }
  }
  if (current) lines.push(current)
  return lines
}

function render() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  // draw background
  if (bgImage.value) {
    // cover resize
    const img = bgImage.value
    const sw = img.width
    const sh = img.height
    const dw = canvas.width
    const dh = canvas.height
    const sRatio = sw / sh
    const dRatio = dw / dh
    let sx = 0, sy = 0, sWidth = sw, sHeight = sh
    if (sRatio > dRatio) {
      // source wider
      sWidth = sh * dRatio
      sx = (sw - sWidth) / 2
    } else {
      // source taller
      sHeight = sw / dRatio
      sy = (sh - sHeight) / 2
    }
    ctx.drawImage(img, sx, sy, sWidth, sHeight, 0, 0, dw, dh)
  } else {
    ctx.fillStyle = '#111827'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
  }

  // text rendering
  ctx.textBaseline = 'top'
  ctx.textAlign = 'left'
  ctx.font = `bold ${fontSize.value}px \"Microsoft YaHei UI\", \"PingFang SC\", Arial`

  const lines = wrapText(title.value, wrapWidth.value)
  // measure heights
  const lineHeights = lines.map(l => fontSize.value)
  const totalHeight = lineHeights.reduce((a, b) => a + b, 0) + (lines.length - 1) * 20
  let y = (canvas.height - totalHeight) / 2

  for (const line of lines) {
    const metrics = ctx.measureText(line)
    const w = metrics.width
    const x = (canvas.width - w) / 2

    if (strokeWidth.value > 0) {
      ctx.lineJoin = 'round'
      ctx.miterLimit = 2
      ctx.lineWidth = strokeWidth.value
      ctx.strokeStyle = strokeColor.value
      ctx.strokeText(line, x, y)
    }
    ctx.fillStyle = fillColor.value
    ctx.fillText(line, x, y)

    y += fontSize.value + 20
  }
}

function download() {
  const canvas = canvasRef.value
  if (!canvas) return
  const link = document.createElement('a')
  link.download = 'cover.png'
  link.href = canvas.toDataURL('image/png')
  link.click()
}

onMounted(() => {
  render()
})

watch([title, canvasWidth, canvasHeight, fontSize, fillColor, strokeColor, strokeWidth, wrapWidth], () => {
  // re-render on changes
  render()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.cover-generator {
  .page-header {
    margin-bottom: 20px;
    h1 {
      font-size: 24px;
      font-weight: 500;
      color: $text-primary;
      margin: 0;
    }
  }

  .panel {
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 20px;
    align-items: start;
  }

  .controls {
    background: #fff;
    padding: 16px;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0,0,0,.1);
  }

  .size-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    max-width: 100%;

    :deep(.el-input-number) {
      width: 160px;
      max-width: 100%;
    }

    .x { color: #909399; }
  }

  .file-name {
    margin-left: 10px;
    color: #909399;
  }

  .preview {
    background: #fff;
    padding: 16px;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0,0,0,.1);
    display: flex;
    justify-content: center;
    align-items: center;
  }

  @media (max-width: 1200px) {
    .panel {
      grid-template-columns: 1fr;
    }
  }
}
</style>


