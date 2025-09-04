<template>
  <div class="hot-products">
    <div class="header">
      <h2>🔥 热门商品</h2>
      <p class="subtitle">精选热销商品，品质保证</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>正在加载热门商品...</p>
    </div>

    <!-- 商品列表 -->
    <div v-else-if="hotProducts.length > 0" class="products-container">
      <div class="products-grid">
        <div 
          v-for="product in hotProducts" 
          :key="product.id"
          class="product-card"
          @click="viewProduct(product)"
        >
          <!-- 商品图片区域 -->
          <div class="product-image">
            <div class="image-placeholder">
              {{ product.name.charAt(0) }}
            </div>
            <div class="hot-label">HOT</div>
            <div class="price-tag">¥{{ product.price }}</div>
          </div>

          <!-- 商品信息 -->
          <div class="product-info">
            <h3 class="product-name">{{ product.name }}</h3>
            <div class="product-meta">
              <span class="brand">{{ product.brand }}</span>
              <span class="category">{{ product.category }}</span>
            </div>
            
            <!-- 规格信息 -->
            <div v-if="product.specifications" class="specs">
              <span 
                v-for="(value, key, index) in getTopSpecs(product.specifications)" 
                :key="key"
                class="spec-item"
                :class="{ 'last': index === Object.keys(getTopSpecs(product.specifications)).length - 1 }"
              >
                {{ value }}
              </span>
            </div>

            <!-- 库存状态 -->
            <div class="stock-info">
              <span 
                class="stock-status" 
                :class="getStockClass(product.stock)"
              >
                {{ getStockText(product.stock) }}
              </span>
              <span class="stock-count">库存: {{ product.stock }}</span>
            </div>
          </div>

          <!-- 悬停效果 -->
          <div class="hover-overlay">
            <button class="view-btn">查看详情</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📦</div>
      <h3>暂无热门商品</h3>
      <p>请稍后再来看看</p>
    </div>

    <!-- 商品详情弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedProduct?.name }}</h2>
          <button @click="closeModal" class="close-btn">×</button>
        </div>
        
        <div v-if="selectedProduct" class="modal-body">
          <div class="product-detail-grid">
            <!-- 左侧：商品图片 -->
            <div class="detail-image">
              <div class="image-large">
                {{ selectedProduct.name.charAt(0) }}
              </div>
            </div>
            
            <!-- 右侧：商品信息 -->
            <div class="detail-info">
              <div class="price-section">
                <span class="current-price">¥{{ selectedProduct.price }}</span>
                <span class="hot-badge">热门</span>
              </div>
              
              <div class="info-section">
                <h4>基本信息</h4>
                <div class="info-grid">
                  <div class="info-item">
                    <span class="label">品牌:</span>
                    <span class="value">{{ selectedProduct.brand }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">分类:</span>
                    <span class="value">{{ selectedProduct.category }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">库存:</span>
                    <span class="value">{{ selectedProduct.stock }} 件</span>
                  </div>
                </div>
              </div>
              
              <!-- 规格参数 -->
              <div v-if="selectedProduct.specifications" class="specs-section">
                <h4>产品规格</h4>
                <div class="specs-grid">
                  <div 
                    v-for="(value, key) in selectedProduct.specifications" 
                    :key="key"
                    class="spec-detail-item"
                  >
                    <span class="spec-name">{{ key }}</span>
                    <span class="spec-val">{{ value }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 商品描述 -->
              <div v-if="selectedProduct.description" class="description-section">
                <h4>商品描述</h4>
                <p class="description-text">{{ selectedProduct.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'HotProducts',
  data() {
    return {
      hotProducts: [],
      loading: true,
      showModal: false,
      selectedProduct: null
    }
  },
  
  mounted() {
    this.loadHotProducts()
  },
  
  methods: {
    async loadHotProducts() {
      this.loading = true
      try {
        const response = await axios.get('http://localhost:8000/api/product/hot/')
        
        if (response.data.code === 200) {
          this.hotProducts = response.data.data
        } else {
          console.error('加载热门商品失败:', response.data.message)
        }
      } catch (error) {
        console.error('网络错误:', error)
        alert('加载热门商品失败，请检查网络连接')
      } finally {
        this.loading = false
      }
    },
    
    async viewProduct(product) {
      this.selectedProduct = product
      this.showModal = true
      
      // 记录用户点击行为
      try {
        await axios.post('http://localhost:8000/api/users/behavior/', {
          user_id: 'U0001', // 这里应该从用户登录状态获取
          product_id: product.product_id,
          action_type: 'click'
        })
      } catch (error) {
        console.error('记录用户行为失败:', error)
      }
    },
    
    closeModal() {
      this.showModal = false
      this.selectedProduct = null
    },
    
    getTopSpecs(specifications) {
      // 只显示前两个规格，避免信息过多
      const entries = Object.entries(specifications)
      const topEntries = entries.slice(0, 2)
      return Object.fromEntries(topEntries)
    },
    
    getStockClass(stock) {
      if (stock > 100) return 'in-stock'
      if (stock > 10) return 'low-stock'
      return 'out-of-stock'
    },
    
    getStockText(stock) {
      if (stock > 100) return '现货充足'
      if (stock > 10) return '库存不多'
      if (stock > 0) return '库存紧张'
      return '暂时缺货'
    }
  }
}
</script>

<style scoped>
.hot-products {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h2 {
  font-size: 28px;
  color: #333;
  margin: 0 0 8px 0;
  font-weight: 700;
}

.subtitle {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #ff6b6b;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.products-container {
  margin-top: 20px;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.product-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.product-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.product-card:hover .hover-overlay {
  opacity: 1;
}

.product-image {
  position: relative;
  height: 200px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.image-placeholder {
  font-size: 56px;
  color: white;
  font-weight: bold;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.hot-label {
  position: absolute;
  top: 12px;
  left: 12px;
  background: linear-gradient(45deg, #ff4757, #ff3742);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 4px rgba(255, 71, 87, 0.3);
}

.price-tag {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 16px;
}

.product-info {
  padding: 20px;
}

.product-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #333;
  line-height: 1.4;
}

.product-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.brand, .category {
  background: #f8f9fa;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
}

.brand {
  background: #e3f2fd;
  color: #1976d2;
}

.specs {
  margin: 12px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.spec-item {
  background: #f0f0f0;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #555;
}

.stock-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.stock-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.stock-status.in-stock {
  background: #d4edda;
  color: #155724;
}

.stock-status.low-stock {
  background: #fff3cd;
  color: #856404;
}

.stock-status.out-of-stock {
  background: #f8d7da;
  color: #721c24;
}

.stock-count {
  font-size: 13px;
  color: #666;
}

.hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.view-btn {
  background: white;
  color: #333;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transform: translateY(10px);
  transition: transform 0.3s ease;
}

.product-card:hover .view-btn {
  transform: translateY(0);
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #666;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #f5f5f5;
}

.modal-body {
  padding: 24px;
}

.product-detail-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
}

.detail-image {
  text-align: center;
}

.image-large {
  width: 180px;
  height: 180px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 72px;
  color: white;
  font-weight: bold;
  margin: 0 auto;
}

.price-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.current-price {
  font-size: 32px;
  font-weight: 700;
  color: #e74c3c;
}

.hot-badge {
  background: #ff4757;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.info-section, .specs-section, .description-section {
  margin-bottom: 24px;
}

.info-section h4, .specs-section h4, .description-section h4 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #333;
}

.info-grid {
  display: grid;
  gap: 8px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.label {
  font-weight: 600;
  color: #666;
  min-width: 60px;
}

.value {
  color: #333;
}

.specs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.spec-detail-item {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.spec-name {
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.spec-val {
  color: #333;
  font-size: 16px;
}

.description-text {
  line-height: 1.6;
  color: #666;
  margin: 0;
}

@media (max-width: 768px) {
  .product-detail-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .detail-image {
    order: -1;
  }
  
  .products-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 16px;
  }
}
</style>

