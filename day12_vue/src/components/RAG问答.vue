<template>
  <div class="rag-chat">
    <div class="chat-header">
      <h2>🤖 智能商品问答</h2>
      <p class="subtitle">基于商品知识库的智能问答系统</p>
      
      <!-- 系统状态 -->
      <div class="system-status">
        <div class="status-item">
          <span class="status-label">系统状态:</span>
          <span :class="['status-value', systemStatus.color]">
            {{ systemStatus.text }}
          </span>
        </div>
        <button @click="initializeSystem" class="init-btn" :disabled="initializing">
          {{ initializing ? '初始化中...' : '重新初始化' }}
        </button>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-container" ref="chatContainer">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-content">
          <h3>👋 欢迎使用智能问答</h3>
          <p>您可以询问关于商品的任何问题，例如：</p>
          <div class="example-questions">
            <button 
              v-for="example in exampleQuestions" 
              :key="example"
              @click="askExample(example)"
              class="example-btn"
            >
              {{ example }}
            </button>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-else class="messages">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message', message.type]"
        >
          <!-- 用户消息 -->
          <div v-if="message.type === 'user'" class="user-message">
            <div class="message-content">
              <p>{{ message.content }}</p>
            </div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          
          <!-- AI回复 -->
          <div v-else class="ai-message">
            <div class="ai-avatar">🤖</div>
            <div class="message-bubble">
              <div class="message-content">
                <p v-if="message.loading" class="loading-text">
                  <span class="typing-indicator"></span>
                  正在思考...
                </p>
                <div v-else>
                  <p class="answer-text">{{ message.content }}</p>
                  
                  <!-- 来源文档 -->
                  <div v-if="message.sources && message.sources.length > 0" class="sources-section">
                    <h4>📚 参考来源:</h4>
                    <div class="sources-list">
                      <div 
                        v-for="(source, idx) in message.sources" 
                        :key="idx"
                        class="source-item"
                      >
                        <div class="source-header">
                          <span class="source-number">{{ idx + 1 }}</span>
                          <span class="source-title">
                            {{ getSourceTitle(source.metadata) }}
                          </span>
                        </div>
                        <div class="source-content">
                          {{ source.content }}
                        </div>
                        <div class="source-meta">
                          <span v-if="source.metadata && source.metadata.product_name">
                            商品: {{ source.metadata.product_name }}
                          </span>
                          <span v-if="source.metadata && source.metadata.brand">
                            品牌: {{ source.metadata.brand }}
                          </span>
                          <span v-if="source.metadata && source.metadata.category">
                            分类: {{ source.metadata.category }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <!-- 相似问题推荐 -->
      <div v-if="similarQuestions.length > 0" class="similar-questions">
        <h4>💡 您可能还想问:</h4>
        <div class="similar-list">
          <button 
            v-for="(question, index) in similarQuestions" 
            :key="index"
            @click="askQuestion(question)"
            class="similar-question-btn"
          >
            {{ question }}
          </button>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-container">
        <div class="input-wrapper">
          <textarea
            v-model="currentQuestion"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.shift.enter.exact="handleShiftEnter"
            placeholder="请输入您的问题... (Enter发送，Shift+Enter换行)"
            class="question-input"
            :disabled="loading"
            ref="questionInput"
          ></textarea>
          <button 
            @click="sendMessage" 
            :disabled="!currentQuestion.trim() || loading"
            class="send-btn"
          >
            <span v-if="loading">⏳</span>
            <span v-else>🚀</span>
          </button>
        </div>
        
        <!-- 快捷操作 -->
        <div class="quick-actions">
          <button @click="clearChat" class="action-btn" :disabled="messages.length === 0">
            🗑️ 清空对话
          </button>
          <button @click="exportChat" class="action-btn" :disabled="messages.length === 0">
            💾 导出对话
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'RAGChat',
  data() {
    return {
      currentQuestion: '',
      messages: [],
      loading: false,
      initializing: false,
      systemStatus: {
        text: '未知',
        color: 'gray'
      },
      similarQuestions: [],
      exampleQuestions: [
        'iPhone 15 Pro有什么特点？',
        'MacBook Pro适合办公吗？',
        'AirPods Pro支持降噪吗？',
        '哪些手机支持5G？',
        '推荐一款游戏耳机'
      ]
    }
  },
  
  mounted() {
    this.checkSystemStatus()
    this.focusInput()
  },
  
  methods: {
    async sendMessage() {
      if (!this.currentQuestion.trim() || this.loading) return
      
      const question = this.currentQuestion.trim()
      this.currentQuestion = ''
      
      // 添加用户消息
      this.addMessage('user', question)
      
      // 添加AI加载消息
      const aiMessageIndex = this.addMessage('ai', '', true)
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom()
      })
      
      try {
        this.loading = true
        
        const response = await axios.post('http://localhost:8000/api/rag/question/', {
          question: question
        })
        
        if (response.data.code === 200) {
          const data = response.data.data
          
          // 更新AI消息
          this.messages[aiMessageIndex].content = data.answer
          this.messages[aiMessageIndex].sources = data.sources || []
          this.messages[aiMessageIndex].loading = false
          
          // 获取相似问题
          this.getSimilarQuestions(question)
          
        } else {
          this.messages[aiMessageIndex].content = response.data.message || '抱歉，处理问题时出现错误'
          this.messages[aiMessageIndex].loading = false
        }
        
      } catch (error) {
        console.error('发送消息失败:', error)
        this.messages[aiMessageIndex].content = '抱歉，网络连接出现问题，请稍后重试'
        this.messages[aiMessageIndex].loading = false
      } finally {
        this.loading = false
        this.$nextTick(() => {
          this.scrollToBottom()
          this.focusInput()
        })
      }
    },
    
    addMessage(type, content, loading = false) {
      const message = {
        type: type,
        content: content,
        timestamp: new Date(),
        loading: loading,
        sources: []
      }
      
      this.messages.push(message)
      return this.messages.length - 1
    },
    
    async askExample(question) {
      this.currentQuestion = question
      await this.sendMessage()
    },
    
    async askQuestion(question) {
      this.currentQuestion = question
      await this.sendMessage()
    },
    
    async getSimilarQuestions(question) {
      try {
        const response = await axios.get('http://localhost:8000/api/rag/similar-questions/', {
          params: { question: question, limit: 3 }
        })
        
        if (response.data.code === 200) {
          this.similarQuestions = response.data.data.similar_questions || []
        }
      } catch (error) {
        console.error('获取相似问题失败:', error)
      }
    },
    
    async initializeSystem() {
      this.initializing = true
      try {
        const response = await axios.post('http://localhost:8000/api/rag/initialize/', {
          force_reload: true
        })
        
        if (response.data.code === 200) {
          this.systemStatus = {
            text: '已就绪',
            color: 'green'
          }
          alert('系统初始化成功！')
        } else {
          this.systemStatus = {
            text: '初始化失败',
            color: 'red'
          }
          alert('系统初始化失败: ' + response.data.message)
        }
      } catch (error) {
        console.error('初始化失败:', error)
        this.systemStatus = {
          text: '连接失败',
          color: 'red'
        }
        alert('初始化失败，请检查网络连接')
      } finally {
        this.initializing = false
      }
    },
    
    async checkSystemStatus() {
      try {
        // 尝试发送一个简单问题来检查系统状态
        const response = await axios.post('http://localhost:8000/api/rag/question/', {
          question: '系统状态检查'
        })
        
        if (response.data.code === 200) {
          this.systemStatus = {
            text: '已就绪',
            color: 'green'
          }
        } else {
          this.systemStatus = {
            text: '需要初始化',
            color: 'orange'
          }
        }
      } catch (error) {
        this.systemStatus = {
          text: '连接失败',
          color: 'red'
        }
      }
    },
    
    clearChat() {
      if (confirm('确定要清空所有对话记录吗？')) {
        this.messages = []
        this.similarQuestions = []
        this.focusInput()
      }
    },
    
    exportChat() {
      try {
        const chatData = this.messages.map(msg => ({
          type: msg.type,
          content: msg.content,
          timestamp: msg.timestamp,
          sources: msg.sources
        }))
        
        const dataStr = JSON.stringify(chatData, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        
        const link = document.createElement('a')
        link.href = URL.createObjectURL(dataBlob)
        link.download = `智能问答对话记录_${new Date().toISOString().slice(0, 10)}.json`
        link.click()
        
      } catch (error) {
        console.error('导出失败:', error)
        alert('导出失败，请重试')
      }
    },
    
    handleShiftEnter(event) {
      // Shift+Enter 允许换行
      return true
    },
    
    scrollToBottom() {
      const container = this.$refs.chatContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    
    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.questionInput) {
          this.$refs.questionInput.focus()
        }
      })
    },
    
    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    getSourceTitle(metadata) {
      if (metadata && metadata.product_name) {
        return metadata.product_name
      } else if (metadata && metadata.parent_category) {
        return metadata.parent_category
      } else {
        return '知识库文档'
      }
    }
  }
}
</script>

<style scoped>
.rag-chat {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 900px;
  margin: 0 auto;
  background: #f5f7fa;
}

.chat-header {
  background: white;
  padding: 20px;
  border-bottom: 1px solid #e1e8ed;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chat-header h2 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 24px;
}

.subtitle {
  color: #666;
  margin: 0 0 16px 0;
  font-size: 14px;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: #666;
}

.status-value {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-value.green {
  background: #d4edda;
  color: #155724;
}

.status-value.orange {
  background: #fff3cd;
  color: #856404;
}

.status-value.red {
  background: #f8d7da;
  color: #721c24;
}

.status-value.gray {
  background: #e9ecef;
  color: #495057;
}

.init-btn {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.init-btn:hover:not(:disabled) {
  background: #0056b3;
}

.init-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
}

.welcome-content h3 {
  color: #333;
  margin-bottom: 16px;
}

.welcome-content p {
  color: #666;
  margin-bottom: 24px;
}

.example-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 400px;
  margin: 0 auto;
}

.example-btn {
  padding: 12px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
}

.example-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  align-items: flex-start;
}

.message.user {
  justify-content: flex-end;
}

.user-message {
  max-width: 70%;
  text-align: right;
}

.user-message .message-content {
  background: #007bff;
  color: white;
  padding: 12px 16px;
  border-radius: 18px 18px 4px 18px;
}

.ai-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 85%;
}

.ai-avatar {
  width: 36px;
  height: 36px;
  background: #6c757d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.message-bubble {
  flex: 1;
}

.ai-message .message-content {
  background: white;
  padding: 16px;
  border-radius: 4px 18px 18px 18px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.user-message .message-time {
  text-align: right;
}

.loading-text {
  color: #666;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 8px;
}

.typing-indicator {
  width: 16px;
  height: 16px;
  border: 2px solid #ccc;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.answer-text {
  line-height: 1.6;
  color: #333;
  margin: 0;
}

.sources-section {
  margin-top: 16px;
  border-top: 1px solid #eee;
  padding-top: 16px;
}

.sources-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
}

.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.source-number {
  background: #007bff;
  color: white;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}

.source-title {
  font-weight: 600;
  color: #333;
}

.source-content {
  color: #555;
  line-height: 1.4;
  margin-bottom: 6px;
}

.source-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #777;
}

.input-area {
  background: white;
  border-top: 1px solid #e1e8ed;
  padding: 16px 20px;
}

.similar-questions {
  margin-bottom: 16px;
}

.similar-questions h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
}

.similar-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.similar-question-btn {
  padding: 4px 8px;
  background: #e9ecef;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  font-size: 12px;
  color: #495057;
  cursor: pointer;
  transition: all 0.2s;
}

.similar-question-btn:hover {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.question-input {
  flex: 1;
  min-height: 40px;
  max-height: 120px;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}

.question-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.question-input:disabled {
  background: #f8f9fa;
  opacity: 0.6;
}

.send-btn {
  padding: 10px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #0056b3;
}

.send-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.quick-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 12px;
  color: #495057;
  cursor: pointer;
}

.action-btn:hover:not(:disabled) {
  background: #e9ecef;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 滚动条样式 */
.chat-container::-webkit-scrollbar {
  width: 6px;
}

.chat-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.chat-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .rag-chat {
    height: 100vh;
  }
  
  .chat-header {
    padding: 16px;
  }
  
  .chat-container {
    padding: 16px;
  }
  
  .input-area {
    padding: 12px 16px;
  }
  
  .ai-message {
    max-width: 95%;
  }
  
  .user-message {
    max-width: 80%;
  }
  
  .example-questions {
    max-width: 100%;
  }
  
  .similar-list {
    flex-direction: column;
  }
  
  .input-wrapper {
    flex-direction: column;
    align-items: stretch;
  }
  
  .send-btn {
    align-self: flex-end;
  }
}
</style>

