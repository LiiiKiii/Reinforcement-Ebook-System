// 研发进度页面JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // 首先加载偏好设置，确保主题在页面渲染前就应用
  if (typeof loadPreferences === 'function') {
    loadPreferences();
  }
  
  // 初始化导航栏（包括主题切换）
  if (typeof setupNavigation === 'function') {
    setupNavigation();
  }
  
  // 初始化滚动渐入效果
  initScrollFadeIn();
});

// 滚动渐入效果 - 使用简化的Intersection Observer，避免频繁更新
function initScrollFadeIn() {
  const fadeElements = document.querySelectorAll('.scroll-fade-in');
  
  if (fadeElements.length === 0) {
    return;
  }
  
  // 使用简单的Intersection Observer，只在元素进入视口时触发一次
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -15% 0px', // 提前15%触发
    threshold: 0.1 // 只检测是否进入视口
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const element = entry.target;
        // 只添加visible类，让CSS处理动画
        element.classList.add('visible');
        // 停止观察，避免重复触发
        observer.unobserve(element);
      }
    });
  }, observerOptions);
  
  // 观察所有需要渐入的元素
  fadeElements.forEach(element => {
    observer.observe(element);
  });
  
  // 处理滚动到底部的情况（功能模块）
  let scrollTimeout = null;
  
  function checkBottom() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 100;
    
    if (isAtBottom) {
      const progressModules = document.querySelector('.progress-modules');
      if (progressModules) {
        const moduleElements = progressModules.querySelectorAll('.scroll-fade-in');
        moduleElements.forEach(element => {
          element.classList.add('visible');
        });
        progressModules.classList.add('visible');
      }
    }
  }
  
  // 使用节流处理底部滚动检测
  window.addEventListener('scroll', () => {
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
    }
    scrollTimeout = setTimeout(checkBottom, 100);
  }, { passive: true });
  
  // 初始检查
  setTimeout(checkBottom, 200);
}
