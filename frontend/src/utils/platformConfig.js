/**
 * 平台配置常量
 * 定义不同平台的标题字数限制和话题数量限制
 */

export const PLATFORM_CONFIG = {
  // 抖音
  DOUYIN: {
    key: 3,
    name: '抖音',
    titleLimit: 30, // 标题字数限制
    topicLimit: 5,  // 话题数量限制
    titlePlaceholder: '请输入标题（最多30字）',
    topicPlaceholder: '最多可添加5个话题'
  },
  // 快手
  KUAISHOU: {
    key: 4,
    name: '快手',
    titleLimit: 30, // 标题字数限制
    topicLimit: 3,   // 话题数量限制
    titlePlaceholder: '请输入标题（最多30字）',
    topicPlaceholder: '最多可添加3个话题'
  },
  // 视频号
  WEIXIN: {
    key: 2,
    name: '视频号',
    titleLimit: 50, // 标题字数限制
    topicLimit: 4,   // 话题数量限制
    titlePlaceholder: '请输入标题（最多50字）',
    topicPlaceholder: '最多可添加4个话题'
  },
  // 小红书
  XIAOHONGSHU: {
    key: 1,
    name: '小红书',
    titleLimit: 20, // 标题字数限制
    topicLimit: 3,   // 话题数量限制
    titlePlaceholder: '请输入标题（最多20字）',
    topicPlaceholder: '最多可添加3个话题'
  }
}

/**
 * 根据平台key获取平台配置
 * @param {number} platformKey 平台key
 * @returns {object} 平台配置对象
 */
export function getPlatformConfig(platformKey) {
  return Object.values(PLATFORM_CONFIG).find(config => config.key === platformKey) || PLATFORM_CONFIG.XIAOHONGSHU
}

/**
 * 获取所有平台配置
 * @returns {array} 所有平台配置数组
 */
export function getAllPlatforms() {
  return Object.values(PLATFORM_CONFIG)
}

/**
 * 验证标题是否符合平台要求
 * @param {string} title 标题内容
 * @param {number} platformKey 平台key
 * @returns {object} 验证结果 {valid: boolean, message: string}
 */
export function validateTitle(title, platformKey) {
  const config = getPlatformConfig(platformKey)
  
  if (!title || !title.trim()) {
    return {
      valid: false,
      message: '请输入标题'
    }
  }
  
  if (title.length > config.titleLimit) {
    return {
      valid: false,
      message: `标题不能超过${config.titleLimit}字，当前${title.length}字`
    }
  }
  
  return {
    valid: true,
    message: ''
  }
}

/**
 * 验证话题数量是否符合平台要求
 * @param {array} topics 话题数组
 * @param {number} platformKey 平台key
 * @returns {object} 验证结果 {valid: boolean, message: string}
 */
export function validateTopics(topics, platformKey) {
  const config = getPlatformConfig(platformKey)
  
  if (!Array.isArray(topics)) {
    return {
      valid: false,
      message: '话题格式错误'
    }
  }
  
  if (topics.length > config.topicLimit) {
    return {
      valid: false,
      message: `最多只能添加${config.topicLimit}个话题，当前${topics.length}个`
    }
  }
  
  return {
    valid: true,
    message: ''
  }
}

/**
 * 验证单个话题内容
 * @param {string} topic 话题内容
 * @returns {object} 验证结果 {valid: boolean, message: string}
 */
export function validateSingleTopic(topic) {
  if (!topic || !topic.trim()) {
    return {
      valid: false,
      message: '话题内容不能为空'
    }
  }
  
  if (topic.length > 20) {
    return {
      valid: false,
      message: '单个话题不能超过20字'
    }
  }
  
  // 检查是否包含特殊字符
  const specialChars = /[<>{}[\]()&$#@!%^*+=|\\/]/g
  if (specialChars.test(topic)) {
    return {
      valid: false,
      message: '话题不能包含特殊字符'
    }
  }
  
  return {
    valid: true,
    message: ''
  }
}
