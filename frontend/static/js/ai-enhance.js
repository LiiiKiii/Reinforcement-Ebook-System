// AI增强页面JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // 使用全局的偏好设置和导航初始化（在 main.js 中定义），避免语言被单独重置
  if (typeof loadPreferences === 'function') {
    loadPreferences();
  }
  if (typeof setupNavigation === 'function') {
    setupNavigation();
  }
  
  // 初始化API key管理
  initAPIKeyManagement();
  
  // 初始化滚动渐入效果
  initScrollFadeIn();
  
  // 页面加载时滚动到顶部
  window.scrollTo(0, 0);
});

// API Key管理
function initAPIKeyManagement() {
  // OpenAI API Key
  const openaiInput = document.getElementById('openai-key');
  const openaiToggle = document.getElementById('openai-toggle');
  const openaiSave = document.getElementById('openai-save');
  const openaiDelete = document.getElementById('openai-delete');
  const openaiStatus = document.getElementById('openai-status');
  
  // 加载已保存的API key
  loadAPIKey('openai', openaiInput, openaiStatus, openaiDelete);
  
  // OpenAI事件处理
  if (openaiToggle) {
    openaiToggle.addEventListener('click', () => {
      togglePasswordVisibility(openaiInput, openaiToggle);
    });
  }
  
  if (openaiSave) {
    openaiSave.addEventListener('click', () => {
      saveAPIKey('openai', openaiInput.value.trim(), openaiStatus, openaiDelete, openaiInput);
    });
  }
  
  if (openaiDelete) {
    openaiDelete.addEventListener('click', () => {
      deleteAPIKey('openai', openaiInput, openaiStatus, openaiDelete);
    });
  }
  
  // 回车键保存
  if (openaiInput) {
    openaiInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        saveAPIKey('openai', openaiInput.value.trim(), openaiStatus, openaiDelete, openaiInput);
      }
    });
  }
}

// 加载API Key
function loadAPIKey(keyName, inputElement, statusElement, deleteButton) {
  const savedKey = localStorage.getItem(`api_key_${keyName}`);
  if (savedKey) {
    inputElement.value = savedKey;
    updateStatus(statusElement, true);
    deleteButton.style.display = 'block';
    // 隐藏输入框内容（显示为密码）
    inputElement.type = 'password';
  } else {
    updateStatus(statusElement, false);
    deleteButton.style.display = 'none';
  }
}

// 保存API Key
function saveAPIKey(keyName, keyValue, statusElement, deleteButton, inputElement) {
  if (!keyValue) {
    alert('请输入API密钥');
    return;
  }
  
  // 基本验证
  if (keyName === 'openai' && !keyValue.startsWith('sk-')) {
    if (!confirm('OpenAI API密钥通常以"sk-"开头，确定要继续保存吗？')) {
      return;
    }
  }
  
  // 保存到localStorage（仅本地存储，不发送到服务器）
  localStorage.setItem(`api_key_${keyName}`, keyValue);
  
  // 更新UI
  updateStatus(statusElement, true);
  deleteButton.style.display = 'block';
  inputElement.type = 'password';
  
  // 显示成功提示
  showMessage('API密钥已保存（仅存储在本地浏览器）', 'success');
}

// 删除API Key
function deleteAPIKey(keyName, inputElement, statusElement, deleteButton) {
  if (!confirm('确定要删除已保存的API密钥吗？')) {
    return;
  }
  
  // 从localStorage删除
  localStorage.removeItem(`api_key_${keyName}`);
  
  // 更新UI
  inputElement.value = '';
  updateStatus(statusElement, false);
  deleteButton.style.display = 'none';
  inputElement.type = 'password';
  
  // 显示提示
  showMessage('API密钥已删除', 'info');
}

// 更新状态显示
function updateStatus(statusElement, isSaved) {
  const lang = (localStorage.getItem('language') || (document.getElementById('html-root')?.getAttribute('lang'))) || 'zh-CN';
  if (isSaved) {
    statusElement.textContent = lang === 'zh-CN' ? '已保存' : 'Saved';
    statusElement.classList.add('saved');
  } else {
    statusElement.textContent = lang === 'zh-CN' ? '未设置' : 'Not set';
    statusElement.classList.remove('saved');
  }
}

// 切换密码显示/隐藏
function togglePasswordVisibility(inputElement, toggleButton) {
  const isPassword = inputElement.type === 'password';
  inputElement.type = isPassword ? 'text' : 'password';
  
  // 更新图标
  const svg = toggleButton.querySelector('svg');
  if (isPassword) {
    // 显示眼睛关闭图标
    svg.innerHTML = `
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
      <line x1="1" y1="1" x2="23" y2="23"></line>
    `;
  } else {
    // 显示眼睛打开图标
    svg.innerHTML = `
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
      <circle cx="12" cy="12" r="3"></circle>
    `;
  }
}

// 显示消息提示
function showMessage(message, type) {
  // 创建消息元素
  const messageEl = document.createElement('div');
  messageEl.className = `api-message api-message-${type}`;
  messageEl.textContent = message;
  
  // 添加到页面
  const container = document.querySelector('.ai-enhance-container');
  if (container) {
    container.appendChild(messageEl);
    
    // 显示动画
    setTimeout(() => {
      messageEl.style.opacity = '1';
      messageEl.style.transform = 'translateY(0)';
    }, 10);
    
    // 3秒后自动移除
    setTimeout(() => {
      messageEl.style.opacity = '0';
      messageEl.style.transform = 'translateY(-10px)';
      setTimeout(() => {
        if (messageEl.parentNode) {
          messageEl.parentNode.removeChild(messageEl);
        }
      }, 300);
    }, 3000);
  }
}

// 滚动渐入效果
function initScrollFadeIn() {
  const fadeElements = document.querySelectorAll('.scroll-fade-in');
  
  if (fadeElements.length === 0) {
    return;
  }
  
  // 获取Hero Section
  const heroSection = document.querySelector('.ai-enhance-hero');
  
  // 初始化：确保所有元素初始状态都是隐藏的
  fadeElements.forEach((element) => {
    // 如果元素在Hero Section内，立即显示（不需要滚动动画）
    if (heroSection && heroSection.contains(element)) {
      element.style.opacity = '1';
      element.style.transform = 'translateY(0)';
      element.classList.add('visible');
    } else {
      element.style.opacity = '0';
      element.style.transform = 'translateY(50px)';
      element.classList.remove('visible');
    }
  });
  
  // 初始检查（延迟一点，确保页面已加载）
  setTimeout(() => {
    checkVisibility();
  }, 100);
  
  // 滚动时检查
  let ticking = false;
  function handleScroll() {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        checkVisibility();
        ticking = false;
      });
      ticking = true;
    }
  }
  
  window.addEventListener('scroll', handleScroll, { passive: true });
  
  function checkVisibility() {
    const windowHeight = window.innerHeight;
    const triggerPoint = windowHeight * 0.8; // 当元素距离视口顶部80%时触发
    const fadeInRange = windowHeight * 0.6; // 渐入范围
    
    fadeElements.forEach((element) => {
      const rect = element.getBoundingClientRect();
      const elementTop = rect.top;
      const elementHeight = rect.height;
      const elementBottom = rect.bottom;
      
      // 特殊处理隐私保护承诺部分，确保它在完全可见时稳定且不抖动
      const isPrivacyNotice = element.classList.contains('privacy-notice');

      // 如果隐私保护承诺已经完成显示，则不再根据滚动反复调整，避免抖动
      if (isPrivacyNotice && element.classList.contains('visible')) {
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
        return;
      }
      
      // 如果元素在视口内或刚刚进入视口
      if (elementTop < triggerPoint && elementTop > -elementHeight) {
        // 计算渐入进度 (0 到 1)
        let progress = Math.max(0, Math.min(1, (triggerPoint - elementTop) / fadeInRange));
        
        // 设置opacity和transform
        element.style.opacity = progress.toString();
        element.style.transform = `translateY(${50 * (1 - progress)}px)`;
        
        // 当完全可见时添加visible类
        if (progress >= 0.9 || (isPrivacyNotice && progress >= 0.5)) {
          element.classList.add('visible');
        }
      } else if (elementTop <= -elementHeight) {
        // 元素已经完全滚过，保持可见
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
        element.classList.add('visible');
      } else {
        // 元素还未进入视口，保持隐藏
        element.style.opacity = '0';
        element.style.transform = 'translateY(50px)';
        element.classList.remove('visible');
      }
    });
  }
}

// ========== 全局API Key获取函数 ==========
// 供其他页面和模块使用

/**
 * 获取保存的API Key
 * @param {string} keyName - API key名称 ('openai')
 * @returns {string|null} - API key字符串，如果不存在则返回null
 */
function getAPIKey(keyName) {
  if (!keyName || typeof keyName !== 'string') {
    console.warn('getAPIKey: 无效的keyName参数');
    return null;
  }
  
  // 目前只支持openai
  if (keyName !== 'openai') {
    console.warn('getAPIKey: 目前只支持 "openai"');
    return null;
  }
  
  const key = localStorage.getItem(`api_key_${keyName}`);
  return key || null;
}

/**
 * 检查API Key是否存在
 * @param {string} keyName - API key名称 ('openai')
 * @returns {boolean} - 如果存在返回true，否则返回false
 */
function hasAPIKey(keyName) {
  return getAPIKey(keyName) !== null;
}

/**
 * 获取所有已保存的API Keys
 * @returns {Object} - 包含所有API keys的对象
 */
function getAllAPIKeys() {
  return {
    openai: getAPIKey('openai')
  };
}

// 将函数暴露到全局作用域，供其他脚本使用
window.getAPIKey = getAPIKey;
window.hasAPIKey = hasAPIKey;
window.getAllAPIKeys = getAllAPIKeys;
