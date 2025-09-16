# PublishCenter 组件重构说明

## 重构概述

本次重构将原本的 `PublishCenter.vue` 单文件组件拆分为多个独立的子组件，提高了代码的可维护性和复用性，并添加了平台配置校验功能。

## 新增文件结构

```
frontend/src/
├── utils/
│   ├── platformConfig.js      # 平台配置常量
│   └── formValidation.js      # 表单验证工具函数
└── components/publish/
    ├── TabManagement.vue      # Tab管理组件
    ├── VideoUpload.vue        # 视频上传组件
    ├── PlatformSelection.vue  # 平台选择组件
    ├── AccountSelection.vue   # 账号选择组件
    ├── TitleInput.vue         # 标题输入组件
    ├── TopicInput.vue         # 话题输入组件
    └── ScheduleSettings.vue   # 定时发布设置组件
```

## 主要功能

### 1. 平台配置校验

- **标题字数限制**：
  - 抖音：55字
  - 快手：30字
  - 视频号：50字
  - 小红书：20字

- **话题数量限制**：
  - 抖音：5个
  - 快手：3个
  - 视频号：4个
  - 小红书：3个

### 2. 实时验证

- 输入时实时显示验证错误
- 平台切换时自动更新限制提示
- 发布前进行完整表单验证

### 3. 组件化设计

- 每个组件职责单一，便于维护
- 组件间通过 props 和 events 通信
- 样式独立，避免样式冲突

## 使用方式

### 平台配置

```javascript
import { getPlatformConfig, validateTitle, validateTopics } from '@/utils/platformConfig'

// 获取平台配置
const config = getPlatformConfig(platformKey)

// 验证标题
const titleValidation = validateTitle(title, platformKey)

// 验证话题
const topicsValidation = validateTopics(topics, platformKey)
```

### 表单验证

```javascript
import { validatePublishForm } from '@/utils/formValidation'

// 验证整个表单
const validation = validatePublishForm(formData)
if (!validation.valid) {
  console.log('验证错误:', validation.errors)
}
```

## 组件特性

### TabManagement
- Tab切换管理
- 添加/删除Tab
- 批量发布功能

### VideoUpload
- 本地上传
- 素材库选择
- 文件管理

### PlatformSelection
- 平台选择
- 平台限制提示
- 平台切换事件

### AccountSelection
- 账号选择
- 平台过滤
- 账号管理

### TitleInput
- 标题输入
- 字数限制
- 实时验证

### TopicInput
- 话题管理
- 自定义话题
- 推荐话题
- 数量限制

### ScheduleSettings
- 定时发布设置
- 时间管理
- 发布数量控制

## 优势

1. **代码复用性**：组件可在其他页面复用
2. **维护性**：单一职责，便于调试和修改
3. **可扩展性**：新增平台或功能时易于扩展
4. **用户体验**：实时验证和提示，提升用户体验
5. **类型安全**：通过验证函数确保数据正确性
