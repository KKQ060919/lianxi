<template>
  <div class="agents-recommendation">
    <div class="header">
      <h2>🤖 智能推荐助手</h2>
      <p class="subtitle">基于您的浏览行为，为您提供个性化商品推荐</p>
    </div>

    <!-- 用户信息设置 -->
    <div class="user-setup-section">
      <div class="user-info-card">
        <h3>👤 用户偏好设置</h3>
        
        <div class="user-input">
          <label>用户ID:</label>
          <input 
            v-model="userId" 
            placeholder="请输入用户ID (如: U0001)"
            class="user-id-input"
          />
        </div>

        <div class="preferences-grid">
          <div class="preference-item">
            <label>偏好分类:</label>
            <div class="category-selection">
              <label 
                v-for="category in availableCategories" 
                :key="category"
                class="category-checkbox"
              >
                <input 
                  type="checkbox" 
                  :value="category"
                  v-model="selectedCategories"
                />
                <span>{{ category }}</span>
              </label>
            </div>
          </div>

          <div class="preference-item">
            <label>价格偏好:</label>
            <select v-model="pricePreference" class="price-select">
              <option value="">请选择价格区间</option>
              <option value="1000-3000">1000-3000元</option>
              <option value="3000-5000">3000-5000元</option>
              <option value="5000-8000">5000-8000元</option>
              <option value="8000-15000">8000-15000元</option>
              <option value="15000+">15000元以上</option>
            </select>
          </div>
        </div>

        <button 
          @click="updateUserProfile" 
          :disabled="!userId || updatingProfile"
          class="update-btn"
        >
          {{ updatingProfile ? '更新中...' : '更新偏好设置' }}
        </button>
      </div>
    </div>

    <!-- 推荐类型选择 -->
    <div class="recommendation-types">
      <h3>📋 推荐类型</h3>
      <div class="type-buttons">
        <button 
          @click="getGeneralRecommendation"
          :disabled="!userId || loading"
          class="type-btn general"
        >
          🎯 通用推荐
        </button>
        
        <button 
          @click="showCategoryModal = true"
          :disabled="!userId || loading"
          class="type-btn category"
        >
          📱 分类推荐
        </button>
        
        <button 
          @click="showPriceModal = true"
          :disabled="!userId || loading"
          class="type-btn price"
        >
          💰 价格推荐
        </button>
        
        <button 
          @click="getCustomRecommendation"
          :disabled="!userId || loading"
          class="type-btn custom"
        >
          ✨ 定制推荐
        </button>
      </div>
    </div>

    <!-- 推荐结果显示 -->
    <div class="recommendation-results">
      <div v-if="loading" class="loading-section">
        <div class="loading-spinner"></div>
        <p>AI正在分析您的偏好，生成个性化推荐...</p>
      </div>

      <div v-else-if="recommendationResult" class="result-section">
        <div class="result-header">
          <h3>💡 推荐结果</h3>
          <div class="result-meta">
            <span class="timestamp">{{ formatTime(recommendationResult.timestamp) }}</span>
            <span class="requirement">需求: {{ recommendationResult.requirement }}</span>
          </div>
        </div>

        <div class="result-content">
          <div class="recommendation-text">
            <pre>{{ recommendationResult.recommendation }}</pre>
          </div>
          
          <!-- 操作按钮 -->
          <div class="result-actions">
            <button @click="copyRecommendation" class="action-btn copy">
              📋 复制推荐
            </button>
            <button @click="exportRecommendation" class="action-btn export">
              💾 导出推荐
            </button>
            <button @click="regenerateRecommendation" class="action-btn regenerate">
              🔄 重新生成
            </button>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">🛍️</div>
        <h3>等待推荐</h3>
        <p>请设置用户偏好并选择推荐类型</p>
      </div>
    </div>

    <!-- 历史推荐记录 -->
    <div v-if="recommendationHistory.length > 0" class="history-section">
      <h3>📚 推荐历史</h3>
      <div class="history-list">
        <div 
          v-for="(item, index) in recommendationHistory" 
          :key="index"
          class="history-item"
          @click="viewHistoryItem(item)"
        >
          <div class="history-header">
            <span class="history-type">{{ item.requirement }}</span>
            <span class="history-time">{{ formatTime(item.timestamp) }}</span>
          </div>
          <p class="history-preview">{{ getPreview(item.recommendation) }}</p>
        </div>
      </div>
    </div>

    <!-- 分类推荐弹窗 -->
    <div v-if="showCategoryModal" class="modal-overlay" @click="showCategoryModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>选择商品分类</h3>
          <button @click="showCategoryModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="category-grid">
            <button 
              v-for="category in availableCategories" 
              :key="category"
              @click="getCategoryRecommendation(category)"
              class="category-modal-btn"
            >
              {{ category }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 价格区间推荐弹窗 -->
    <div v-if="showPriceModal" class="modal-overlay" @click="showPriceModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>选择价格区间</h3>
          <button @click="showPriceModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="price-input-section">
            <div class="price-inputs">
              <div class="input-group">
                <label>最低价格:</label>
                <input 
                  v-model.number="customMinPrice" 
                  type="number" 
                  placeholder="0"
                  class="price-input"
                />
              </div>
              <div class="input-group">
                <label>最高价格:</label>
                <input 
                  v-model.number="customMaxPrice" 
                  type="number" 
                  placeholder="10000"
                  class="price-input"
                />
              </div>
            </div>
            <button 
              @click="getPriceRangeRecommendation"
              :disabled="!customMinPrice || !customMaxPrice"
              class="price-confirm-btn"
            >
              获取推荐
            </button>
          </div>
          
          <!-- 预设价格区间 -->
          <div class="preset-prices">
            <h4>快速选择:</h4>
            <div class="preset-grid">
              <button @click="selectPresetPrice(1000, 3000)" class="preset-btn">1000-3000</button>
              <button @click="selectPresetPrice(3000, 5000)" class="preset-btn">3000-5000</button>
              <button @click="selectPresetPrice(5000, 8000)" class="preset-btn">5000-8000</button>
              <button @click="selectPresetPrice(8000, 15000)" class="preset-btn">8000-15000</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 定制推荐弹窗 -->
    <div v-if="showCustomModal" class="modal-overlay" @click="showCustomModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>定制推荐需求</h3>
          <button @click="showCustomModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <textarea 
            v-model="customRequirement"
            placeholder="请描述您的具体需求，例如：推荐适合学生使用的手机、推荐性价比高的耳机等..."
            class="custom-textarea"
          ></textarea>
          <button 
            @click="submitCustomRecommendation"
            :disabled="!customRequirement.trim()"
            class="custom-submit-btn"
          >
            获取定制推荐
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AgentsRecommendation',
  data() {
    return {
      userId: 'U0001',
      selectedCategories: [],
      pricePreference: '',
      availableCategories: ['手机', '耳机', '电脑', '平板', '智能手表', '音响'],
      
      loading: false,
      updatingProfile: false,
      recommendationResult: null,
      recommendationHistory: [],
      
      // 弹窗控制
      showCategoryModal: false,
      showPriceModal: false,
      showCustomModal: false,
      
      // 价格推荐
      customMinPrice: null,
      customMaxPrice: null,
      
      // 定制推荐
      customRequirement: ''
    }
  },
  
  mounted() {
    this.loadUserProfile()
  },
  
  methods: {
    async loadUserProfile() {
      if (!this.userId) return
      
      try {
        const response = await axios.get(`http://localhost:8000/api/agents/profile/${this.userId}/`)
        
        if (response.data.code === 200) {
          const data = response.data.data
          this.selectedCategories = data.preferred_categories || []
          this.pricePreference = data.price_preference || ''
        }
      } catch (error) {
        console.log('用户画像不存在，将创建新的画像')
      }
    },
    
    async updateUserProfile() {
      this.updatingProfile = true
      try {
        const response = await axios.post('http://localhost:8000/api/agents/profile/', {
          user_id: this.userId,
          preferred_categories: this.selectedCategories,
          price_preference: this.pricePreference
        })
        
        if (response.data.code === 200) {
          alert('用户偏好设置更新成功！')
        } else {
          alert('更新失败: ' + response.data.message)
        }
      } catch (error) {
        console.error('更新失败:', error)
        alert('网络错误，请重试')
      } finally {
        this.updatingProfile = false
      }
    },
    
    async getGeneralRecommendation() {
      await this.getRecommendation('推荐适合我的商品')
    },
    
    async getCategoryRecommendation(category) {
      this.showCategoryModal = false
      await this.getRecommendation(`推荐${category}类别的商品`)
    },
    
    async getPriceRangeRecommendation() {
      if (!this.customMinPrice || !this.customMaxPrice) return
      
      this.showPriceModal = false
      await this.getRecommendation(`推荐价格在${this.customMinPrice}到${this.customMaxPrice}元之间的商品`)
    },
    
    async getCustomRecommendation() {
      this.showCustomModal = true
    },
    
    async submitCustomRecommendation() {
      if (!this.customRequirement.trim()) return
      
      this.showCustomModal = false
      await this.getRecommendation(this.customRequirement)
      this.customRequirement = ''
    },
    
    async getRecommendation(requirement) {
      this.loading = true
      try {
        const response = await axios.post('http://localhost:8000/api/agents/recommend/', {
          user_id: this.userId,
          requirement: requirement
        })
        
        if (response.data.code === 200) {
          this.recommendationResult = response.data.data
          
          // 添加到历史记录
          this.recommendationHistory.unshift({
            ...response.data.data,
            id: Date.now()
          })
          
          // 只保留最近10条记录
          if (this.recommendationHistory.length > 10) {
            this.recommendationHistory = this.recommendationHistory.slice(0, 10)
          }
          
        } else {
          alert('推荐失败: ' + response.data.message)
        }
      } catch (error) {
        console.error('推荐失败:', error)
        alert('网络错误，请重试')
      } finally {
        this.loading = false
      }
    },
    
    async regenerateRecommendation() {
      if (this.recommendationResult) {
        await this.getRecommendation(this.recommendationResult.requirement)
      }
    },
    
    selectPresetPrice(min, max) {
      this.customMinPrice = min
      this.customMaxPrice = max
      this.getPriceRangeRecommendation()
    },
    
    copyRecommendation() {
      if (this.recommendationResult) {
        navigator.clipboard.writeText(this.recommendationResult.recommendation).then(() => {
          alert('推荐内容已复制到剪贴板')
        })
      }
    },
    
    exportRecommendation() {
      if (this.recommendationResult) {
        const data = JSON.stringify(this.recommendationResult, null, 2)
        const blob = new Blob([data], { type: 'application/json' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `推荐结果_${new Date().toISOString().slice(0, 10)}.json`
        link.click()
      }
    },
    
    viewHistoryItem(item) {
      this.recommendationResult = item
    },
    
    formatTime(timestamp) {
      return new Date(timestamp).toLocaleString('zh-CN')
    },
    
    getPreview(text) {
      return text.length > 100 ? text.slice(0, 100) + '...' : text
    }
  }
}
</script>

<style scoped>
.agents-recommendation {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.header {
  text-align: center;
  margin-bottom: 30px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header h2 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 28px;
}

.subtitle {
  color: #666;
  margin: 0;
  font-size: 16px;
}

.user-setup-section {
  margin-bottom: 24px;
}

.user-info-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.user-info-card h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.user-input {
  margin-bottom: 20px;
}

.user-input label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}

.user-id-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.preferences-grid {
  display: grid;
  gap: 20px;
  margin-bottom: 20px;
}

.preference-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}

.category-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.category-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-weight: normal;
}

.category-checkbox input {
  margin: 0;
}

.price-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.update-btn {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.update-btn:hover:not(:disabled) {
  background: #0056b3;
}

.update-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.recommendation-types {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 24px;
}

.recommendation-types h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.type-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.type-btn {
  padding: 12px 16px;
  border: 2px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.type-btn.general {
  background: #e3f2fd;
  color: #1976d2;
  border-color: #1976d2;
}

.type-btn.category {
  background: #f3e5f5;
  color: #7b1fa2;
  border-color: #7b1fa2;
}

.type-btn.price {
  background: #e8f5e8;
  color: #388e3c;
  border-color: #388e3c;
}

.type-btn.custom {
  background: #fff3e0;
  color: #f57c00;
  border-color: #f57c00;
}

.type-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.type-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.recommendation-results {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 24px;
  overflow: hidden;
}

.loading-section {
  padding: 60px 20px;
  text-align: center;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result-section {
  padding: 24px;
}

.result-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 16px;
}

.result-header h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.result-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #666;
}

.recommendation-text {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #007bff;
  margin-bottom: 20px;
}

.recommendation-text pre {
  white-space: pre-wrap;
  margin: 0;
  font-family: inherit;
  line-height: 1.6;
  color: #333;
}

.result-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.history-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.history-section h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-type {
  font-weight: 600;
  color: #333;
}

.history-time {
  font-size: 12px;
  color: #999;
}

.history-preview {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
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
  border-radius: 12px;
  max-width: 500px;
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

.modal-header h3 {
  margin: 0;
  color: #333;
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

.modal-body {
  padding: 20px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.category-modal-btn {
  padding: 12px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-modal-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.price-input-section {
  margin-bottom: 20px;
}

.price-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 600;
  color: #555;
}

.price-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.price-confirm-btn {
  width: 100%;
  padding: 10px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.price-confirm-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.preset-prices h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.preset-btn {
  padding: 8px;
  background: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.preset-btn:hover {
  background: #007bff;
  color: white;
}

.custom-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  resize: vertical;
  font-family: inherit;
  margin-bottom: 16px;
}

.custom-submit-btn {
  width: 100%;
  padding: 12px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.custom-submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .agents-recommendation {
    padding: 12px;
  }
  
  .type-buttons {
    grid-template-columns: 1fr;
  }
  
  .preferences-grid {
    grid-template-columns: 1fr;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .action-btn {
    width: 100%;
  }
  
  .price-inputs {
    grid-template-columns: 1fr;
  }
  
  .preset-grid {
    grid-template-columns: 1fr;
  }
}
</style>

