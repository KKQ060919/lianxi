<template>
  <div class="product-page">
    <!-- 顶部搜索栏 -->
    <div class="search-bar">
      <div class="search-input-wrapper">
        <input 
          v-model="searchQuery" 
          @keyup.enter="searchProducts"
          placeholder="搜索商品..."
          class="search-input"
        />
        <button @click="searchProducts" class="search-btn">搜索</button>
      </div>
      
      <!-- 筛选条件 -->
      <div class="filters">
        <select v-model="selectedCategory" @change="filterProducts" class="filter-select">
          <option value="">所有分类</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
        
        <select v-model="selectedBrand" @change="filterProducts" class="filter-select">
          <option value="">所有品牌</option>
          <option v-for="brand in brands" :key="brand" :value="brand">
            {{ brand }}
          </option>
        </select>
      </div>
    </div>

    <!-- 商品列表 -->
    <div class="products-container">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="products.length === 0" class="no-products">暂无商品</div>
      <div v-else class="products-grid">
        <div 
          v-for="product in products" 
          :key="product.id"
          class="product-card"
          @click="viewProductDetail(product)"
        >
          <div class="product-image">
            <div class="image-placeholder">{{ product.name.charAt(0) }}</div>
            <div v-if="product.is_hot" class="hot-badge">热门</div>
          </div>
          
          <div class="product-info">
            <h3 class="product-name">{{ product.name }}</h3>
            <p class="product-brand">{{ product.brand }}</p>
            <p class="product-category">{{ product.category }}</p>
            
            <!-- 规格显示 -->
            <div class="specifications" v-if="product.specifications">
              <span 
                v-for="(value, key) in product.specifications" 
                :key="key"
                class="spec-tag"
              >
                {{ key }}: {{ value }}
              </span>
            </div>
            
            <div class="product-bottom">
              <span class="product-price">¥{{ product.price }}</span>
              <span class="product-stock">库存: {{ product.stock }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页组件 -->
    <div v-if="pagination && pagination.total_pages > 1" class="pagination">
      <button 
        @click="loadPage(pagination.current_page - 1)"
        :disabled="!pagination.has_previous"
        class="page-btn"
      >
        上一页
      </button>
      
      <span class="page-info">
        第 {{ pagination.current_page }} 页 / 共 {{ pagination.total_pages }} 页
        (总计 {{ pagination.total_count }} 个商品)
      </span>
      
      <button 
        @click="loadPage(pagination.current_page + 1)"
        :disabled="!pagination.has_next"
        class="page-btn"
      >
        下一页
      </button>
    </div>

    <!-- 商品详情弹窗 -->
    <div v-if="showDetail" class="modal-overlay" @click="closeDetail">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>商品详情</h2>
          <button @click="closeDetail" class="close-btn">×</button>
        </div>
        
        <div v-if="selectedProduct" class="product-detail">
          <div class="detail-main">
            <h3>{{ selectedProduct.name }}</h3>
            <p><strong>品牌:</strong> {{ selectedProduct.brand }}</p>
            <p><strong>分类:</strong> {{ selectedProduct.category }}</p>
            <p><strong>价格:</strong> ¥{{ selectedProduct.price }}</p>
            <p><strong>库存:</strong> {{ selectedProduct.stock }}</p>
            
            <!-- 规格详情 -->
            <div v-if="selectedProduct.specifications" class="specs-detail">
              <h4>产品规格:</h4>
              <div class="specs-grid">
                <div 
                  v-for="(value, key) in selectedProduct.specifications" 
                  :key="key"
                  class="spec-item"
                >
                  <span class="spec-key">{{ key }}:</span>
                  <span class="spec-value">{{ value }}</span>
                </div>
              </div>
            </div>
            
            <!-- 商品描述 -->
            <div v-if="selectedProduct.description" class="description">
              <h4>商品描述:</h4>
              <p>{{ selectedProduct.description }}</p>
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
  name: 'ProductPage',
  data() {
    return {
      products: [],
      categories: [],
      brands: [],
      pagination: null,
      loading: false,
      searchQuery: '',
      selectedCategory: '',
      selectedBrand: '',
      currentPage: 1,
      pageSize: 12,
      showDetail: false,
      selectedProduct: null
    }
  },
  
  mounted() {
    this.loadInitialData()
  },
  
  methods: {
    async loadInitialData() {
      // 并行加载所有初始数据
      await Promise.all([
        this.loadProducts(),
        this.loadCategories(),
        this.loadBrands()
      ])
    },
    
    async loadProducts(page = 1) {
      this.loading = true
      try {
        const params = {
          page: page,
          page_size: this.pageSize
        }
        
        if (this.searchQuery) params.search = this.searchQuery
        if (this.selectedCategory) params.category = this.selectedCategory
        if (this.selectedBrand) params.brand = this.selectedBrand
        
        const response = await axios.get('http://localhost:8000/api/product/list/', { params })
        
        if (response.data.code === 200) {
          this.products = response.data.data.products
          this.pagination = response.data.data.pagination
          this.currentPage = page
        }
      } catch (error) {
        console.error('加载商品失败:', error)
        alert('加载商品失败，请重试')
      } finally {
        this.loading = false
      }
    },
    
    async loadCategories() {
      try {
        const response = await axios.get('http://localhost:8000/api/product/categories/')
        if (response.data.code === 200) {
          this.categories = response.data.data
        }
      } catch (error) {
        console.error('加载分类失败:', error)
      }
    },
    
    async loadBrands() {
      try {
        const response = await axios.get('http://localhost:8000/api/product/brands/')
        if (response.data.code === 200) {
          this.brands = response.data.data
        }
      } catch (error) {
        console.error('加载品牌失败:', error)
      }
    },
    
    searchProducts() {
      this.currentPage = 1
      this.loadProducts(1)
    },
    
    filterProducts() {
      this.currentPage = 1
      this.loadProducts(1)
    },
    
    loadPage(page) {
      if (page >= 1 && page <= this.pagination.total_pages) {
        this.loadProducts(page)
      }
    },
    
    async viewProductDetail(product) {
      this.selectedProduct = product
      this.showDetail = true
      
      // 记录用户浏览行为
      try {
        await axios.post('http://localhost:8000/api/users/behavior/', {
          user_id: 'U0001', // 这里应该是当前登录用户的ID
          product_id: product.product_id,
          action_type: 'view'
        })
      } catch (error) {
        console.error('记录浏览行为失败:', error)
      }
    },
    
    closeDetail() {
      this.showDetail = false
      this.selectedProduct = null
    }
  }
}
</script>

<style scoped>
.product-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.search-bar {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.search-input-wrapper {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.search-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
}

.search-btn {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.search-btn:hover {
  background: #0056b3;
}

.filters {
  display: flex;
  gap: 15px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.products-container {
  min-height: 400px;
}

.loading, .no-products {
  text-align: center;
  padding: 60px 20px;
  font-size: 18px;
  color: #666;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.product-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.product-image {
  position: relative;
  height: 180px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-placeholder {
  font-size: 48px;
  color: white;
  font-weight: bold;
}

.hot-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #ff4757;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.product-info {
  padding: 16px;
}

.product-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
}

.product-brand, .product-category {
  font-size: 14px;
  color: #666;
  margin: 4px 0;
}

.specifications {
  margin: 10px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.spec-tag {
  background: #f8f9fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.product-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.product-price {
  font-size: 20px;
  font-weight: 600;
  color: #e74c3c;
}

.product-stock {
  font-size: 14px;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
  padding: 20px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  border-radius: 4px;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-detail {
  padding: 20px;
}

.detail-main h3 {
  margin-top: 0;
  font-size: 24px;
  color: #333;
}

.detail-main p {
  margin: 8px 0;
  line-height: 1.5;
}

.specs-detail, .description {
  margin-top: 20px;
}

.specs-detail h4, .description h4 {
  margin-bottom: 10px;
  color: #333;
}

.specs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.spec-item {
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 4px;
}

.spec-key {
  font-weight: 600;
  color: #333;
}

.spec-value {
  color: #666;
  margin-left: 8px;
}

.description p {
  color: #666;
  line-height: 1.6;
}
</style>

