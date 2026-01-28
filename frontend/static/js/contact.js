// 加入我们页面JavaScript

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

// 滚动渐入效果
function initScrollFadeIn() {
  // 处理contact-section（表单部分）和scroll-fade-in元素
  const contactSection = document.querySelector('.contact-section');
  const fadeElements = document.querySelectorAll('.scroll-fade-in');
  const allElements = contactSection ? [contactSection, ...fadeElements] : [...fadeElements];
  
  if (allElements.length === 0) {
    return;
  }
  
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
    const triggerPoint = windowHeight * 0.8;
    const fadeInRange = windowHeight * 0.6;
    
    allElements.forEach((element) => {
      const rect = element.getBoundingClientRect();
      const elementTop = rect.top;
      const elementHeight = rect.height;
      const elementBottom = rect.bottom;
      
      // 如果元素在视口内，使用渐入效果
      if (elementTop < triggerPoint && elementTop > -elementHeight) {
        const progress = Math.max(0, Math.min(1, (triggerPoint - elementTop) / fadeInRange));
        element.style.opacity = progress.toString();
        element.style.transform = `translateY(${50 * (1 - progress)}px)`;
        
        if (progress >= 0.9) {
          element.classList.add('visible');
        }
      } else if (elementTop <= -elementHeight) {
        // 元素已经完全滚过，保持可见
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
        element.classList.add('visible');
      } else if (elementTop < windowHeight && elementBottom > 0) {
        // 元素在视口内但还未触发渐入，开始渐入
        const progress = Math.max(0, Math.min(1, (windowHeight - elementTop) / fadeInRange));
        element.style.opacity = progress.toString();
        element.style.transform = `translateY(${50 * (1 - progress)}px)`;
        
        if (progress >= 0.9) {
          element.classList.add('visible');
        }
      }
    });
  }
  
  // 初始检查 - 立即执行，确保可见内容显示
  checkVisibility();
}
