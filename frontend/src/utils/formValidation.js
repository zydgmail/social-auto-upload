/**
 * 表单验证工具函数
 * 提供统一的表单验证逻辑
 */

import { validateTitle, validateTopics, validateSingleTopic } from './platformConfig'

/**
 * 验证发布表单
 * @param {object} formData 表单数据
 * @returns {object} 验证结果 {valid: boolean, errors: object}
 */
export function validatePublishForm(formData) {
  const errors = {}
  let isValid = true

  // 验证文件列表
  if (!formData.fileList || formData.fileList.length === 0) {
    errors.fileList = '请先上传视频文件'
    isValid = false
  }

  // 验证标题
  const titleValidation = validateTitle(formData.title, formData.selectedPlatform)
  if (!titleValidation.valid) {
    errors.title = titleValidation.message
    isValid = false
  }

  // 验证平台
  if (!formData.selectedPlatform) {
    errors.platform = '请选择发布平台'
    isValid = false
  }

  // 验证账号
  if (!formData.selectedAccounts || formData.selectedAccounts.length === 0) {
    errors.accounts = '请选择发布账号'
    isValid = false
  }

  // 验证话题
  const topicsValidation = validateTopics(formData.selectedTopics, formData.selectedPlatform)
  if (!topicsValidation.valid) {
    errors.topics = topicsValidation.message
    isValid = false
  }

  // 验证定时发布设置
  if (formData.scheduleEnabled) {
    if (!formData.videosPerDay || formData.videosPerDay < 1 || formData.videosPerDay > 55) {
      errors.videosPerDay = '每天发布视频数必须在1-55之间'
      isValid = false
    }

    if (!formData.dailyTimes || formData.dailyTimes.length === 0) {
      errors.dailyTimes = '请设置发布时间'
      isValid = false
    }

    if (formData.dailyTimes && formData.dailyTimes.length !== formData.videosPerDay) {
      errors.dailyTimes = '发布时间数量必须与每天发布视频数一致'
      isValid = false
    }

    if (formData.startDays === undefined || formData.startDays < 0) {
      errors.startDays = '请选择开始天数'
      isValid = false
    }
  }

  return {
    valid: isValid,
    errors: errors
  }
}

/**
 * 验证单个字段
 * @param {string} fieldName 字段名
 * @param {any} value 字段值
 * @param {object} context 上下文数据（如平台信息）
 * @returns {object} 验证结果 {valid: boolean, message: string}
 */
export function validateField(fieldName, value, context = {}) {
  switch (fieldName) {
    case 'title':
      return validateTitle(value, context.platformKey)
    
    case 'topics':
      return validateTopics(value, context.platformKey)
    
    case 'singleTopic':
      return validateSingleTopic(value)
    
    case 'fileList':
      if (!value || value.length === 0) {
        return { valid: false, message: '请先上传视频文件' }
      }
      return { valid: true, message: '' }
    
    case 'platform':
      if (!value) {
        return { valid: false, message: '请选择发布平台' }
      }
      return { valid: true, message: '' }
    
    case 'accounts':
      if (!value || value.length === 0) {
        return { valid: false, message: '请选择发布账号' }
      }
      return { valid: true, message: '' }
    
    case 'videosPerDay':
      if (!value || value < 1 || value > 55) {
        return { valid: false, message: '每天发布视频数必须在1-55之间' }
      }
      return { valid: true, message: '' }
    
    case 'dailyTimes':
      if (!value || value.length === 0) {
        return { valid: false, message: '请设置发布时间' }
      }
      return { valid: true, message: '' }
    
    case 'startDays':
      if (value === undefined || value < 0) {
        return { valid: false, message: '请选择开始天数' }
      }
      return { valid: true, message: '' }
    
    default:
      return { valid: true, message: '' }
  }
}

/**
 * 实时验证表单字段
 * @param {string} fieldName 字段名
 * @param {any} value 字段值
 * @param {object} formData 完整表单数据
 * @returns {object} 验证结果 {valid: boolean, message: string}
 */
export function validateFieldRealtime(fieldName, value, formData) {
  const context = {
    platformKey: formData.selectedPlatform
  }
  
  return validateField(fieldName, value, context)
}

/**
 * 获取字段验证规则
 * @param {string} fieldName 字段名
 * @param {object} context 上下文数据
 * @returns {object} 验证规则
 */
export function getFieldValidationRules(fieldName, context = {}) {
  switch (fieldName) {
    case 'title':
      return {
        required: true,
        maxLength: context.platformConfig?.titleLimit || 100,
        message: `标题不能超过${context.platformConfig?.titleLimit || 100}字`
      }
    
    case 'topics':
      return {
        maxCount: context.platformConfig?.topicLimit || 5,
        message: `最多只能添加${context.platformConfig?.topicLimit || 5}个话题`
      }
    
    case 'fileList':
      return {
        required: true,
        minCount: 1,
        message: '请至少上传一个视频文件'
      }
    
    case 'platform':
      return {
        required: true,
        message: '请选择发布平台'
      }
    
    case 'accounts':
      return {
        required: true,
        minCount: 1,
        message: '请至少选择一个账号'
      }
    
    default:
      return {}
  }
}

/**
 * 批量验证多个字段
 * @param {object} fields 字段对象 {fieldName: value}
 * @param {object} context 上下文数据
 * @returns {object} 验证结果 {valid: boolean, errors: object}
 */
export function validateFields(fields, context = {}) {
  const errors = {}
  let isValid = true

  for (const [fieldName, value] of Object.entries(fields)) {
    const validation = validateField(fieldName, value, context)
    if (!validation.valid) {
      errors[fieldName] = validation.message
      isValid = false
    }
  }

  return {
    valid: isValid,
    errors: errors
  }
}
