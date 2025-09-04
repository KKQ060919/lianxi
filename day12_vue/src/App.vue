<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentRoute = ref('')

// 监听路由变化
router.afterEach((to) => {
  currentRoute.value = to.name
})

const navigationItems = [
  { name: 'Home', label: '🏠 首页', path: '/' },
  { name: 'HotProducts', label: '🔥 热门商品', path: '/hot-products' },
  { name: 'Products', label: '🛍️ 商品页面', path: '/products' },
  { name: 'RAGChat', label: '🤖 智能问答', path: '/rag-chat' },
  { name: 'AgentsChat', label: '✨ 智能推荐', path: '/agents-chat' }
]

const navigateTo = (path) => {
  router.push(path)
}
</script>

<template>
  <div id="app">
    <!-- 导航栏 -->
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-brand">
          <h2>🛒 智能商城系统</h2>
        </div>
        
        <div class="nav-menu">
          <button 
            v-for="item in navigationItems" 
            :key="item.name"
            @click="navigateTo(item.path)"
            :class="['nav-item', { active: currentRoute === item.name }]"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </nav>
    
    <!-- 主要内容区域 -->
    <main class="main-content">
      <router-view />
    </main>
    
    <!-- 页脚 -->
    <footer class="footer">
      <p>&copy; 2024 智能商城系统 - 基于Django + Vue + RAG + Agents技术栈</p>
    </footer>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
  color: #333;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
}

.nav-brand h2 {
  color: #007bff;
  font-size: 20px;
  font-weight: 700;
}

.nav-menu {
  display: flex;
  gap: 8px;
}

.nav-item {
  padding: 8px 16px;
  background: none;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  transition: all 0.2s ease;
}

.nav-item:hover {
  color: #007bff;
  background: #f8f9fa;
  border-color: #e3f2fd;
}

.nav-item.active {
  color: #007bff;
  background: #e3f2fd;
  border-color: #007bff;
  font-weight: 600;
}

.main-content {
  flex: 1;
  min-height: calc(100vh - 140px);
}

.footer {
  background: #343a40;
  color: white;
  text-align: center;
  padding: 20px;
  margin-top: auto;
}

.footer p {
  margin: 0;
  font-size: 14px;
  opacity: 0.8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    height: auto;
    padding: 16px 20px;
    gap: 16px;
  }
  
  .nav-brand h2 {
    font-size: 18px;
  }
  
  .nav-menu {
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px;
  }
  
  .nav-item {
    padding: 6px 12px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .nav-menu {
    flex-direction: column;
    width: 100%;
  }
  
  .nav-item {
    width: 100%;
    text-align: center;
  }
}

/* 全局滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 全局动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 工具类 */
.text-center {
  text-align: center;
}

.mb-20 {
  margin-bottom: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.p-20 {
  padding: 20px;
}

.rounded {
  border-radius: 8px;
}

.shadow {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #1e7e34;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}
</style>