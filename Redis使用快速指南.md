# Redis功能使用快速指南

## 🚀 快速开始

### 1. 启动Redis服务
```bash
# Windows (如果安装了Redis)
redis-server

# 或者使用Docker
docker run -d -p 6379:6379 redis:latest
```

### 2. 运行功能测试
```bash
python test_redis_integration.py
```

## 💬 RAG对话功能使用

### 基本问答（带存储）
```python
import requests

# 发送问题并自动存储到Redis
response = requests.post('http://localhost:8000/rag/question/', json={
    'question': 'iPhone 15有什么特点？',
    'user_id': 'user123',  # 可选：注册用户
    'session_id': 'session456'  # 可选：匿名用户会话
})

result = response.json()
print(f"回答: {result['data']['answer']}")
print(f"对话ID: {result['data']['conversation_id']}")  # 新增字段
```

### 获取对话历史
```python
# 获取用户的对话历史
response = requests.get('http://localhost:8000/rag/conversations/', params={
    'user_id': 'user123',
    'limit': 10
})

conversations = response.json()['data']['conversations']
for conv in conversations:
    print(f"Q: {conv['question']}")
    print(f"时间: {conv['created_at']}")
```

### 查看热门问题
```python
# 获取最热门的问题
response = requests.get('http://localhost:8000/rag/popular-questions/', params={
    'limit': 5
})

questions = response.json()['data']['popular_questions']
for q in questions:
    print(f"{q['question']} (问过{q['count']}次)")
```

## 🎯 智能推荐功能使用

### 获取个性化推荐（带存储）
```python
import requests

# 获取推荐并自动存储到Redis
response = requests.post('http://localhost:8000/agents/recommend/', json={
    'user_id': 'user123',
    'requirement': '推荐性价比高的手机',
    'session_id': 'session456'  # 可选：匿名用户
})

result = response.json()
print(f"推荐内容: {result['data']['recommendation']}")
print(f"推荐ID: {result['data']['recommendation_id']}")  # 新增字段
```

### 获取推荐历史
```python
# 获取用户的推荐历史
response = requests.get('http://localhost:8000/agents/history/', params={
    'user_id': 'user123',
    'limit': 10
})

recommendations = response.json()['data']['recommendations']
for rec in recommendations:
    print(f"需求: {rec['requirement']}")
    print(f"商品数: {rec['product_count']}")
    print(f"时间: {rec['created_at']}")
```

### 查看热门需求
```python
# 获取最热门的需求
response = requests.get('http://localhost:8000/agents/popular-requirements/', params={
    'limit': 5
})

requirements = response.json()['data']['popular_requirements']
for req in requirements:
    print(f"{req['requirement']} (需求过{req['count']}次)")
```

## 🔧 高级功能

### 1. 删除历史记录
```python
# 删除特定对话
requests.delete('http://localhost:8000/rag/conversations/', json={
    'conversation_id': 'conv_1234567890',
    'user_id': 'user123'
})

# 删除特定推荐记录
requests.delete('http://localhost:8000/agents/history/', json={
    'recommendation_id': 'rec_1234567890',
    'user_id': 'user123'
})
```

### 2. 搜索历史记录
```python
from rag.redis import RAGConversationCache
from Agents.redis import RecommendationCache

# 搜索包含特定关键词的对话
conversations = RAGConversationCache.search_conversations(
    user_id='user123',
    keyword='iPhone',
    limit=10
)

# 搜索包含特定关键词的推荐
recommendations = RecommendationCache.search_recommendations(
    user_id='user123', 
    keyword='手机',
    limit=10
)
```

### 3. 用户偏好管理
```python
# 保存用户偏好
RecommendationCache.save_user_preferences('user123', {
    'preferred_categories': ['手机', '耳机', '电脑'],
    'price_preference': '2000-6000',
    'brand_preference': ['苹果', '华为', '小米']
})

# 获取用户偏好
preferences = RecommendationCache.get_user_preferences('user123')
print(f"偏好分类: {preferences['preferred_categories']}")
```

### 4. 统计信息查询
```python
# 获取对话统计
stats = RAGConversationCache.get_conversation_statistics('user123')
print(f"总对话数: {stats['total_conversations']}")

# 获取推荐统计
stats = RecommendationCache.get_user_recommendation_statistics('user123')
print(f"总推荐数: {stats['total_recommendations']}")

# 获取全局推荐统计
global_stats = RecommendationCache.get_recommendation_stats()
print(f"今日推荐总数: {global_stats['daily_recommendations']}")
```

## 📊 数据结构说明

### 对话记录数据结构
```json
{
    "conversation_id": "conv_1234567890",
    "user_id": "user123",
    "session_id": "session456",
    "question": "用户问题",
    "answer": "AI回答",
    "sources": ["知识来源列表"],
    "timestamp": 1641024000,
    "created_at": "2022-01-01T12:00:00",
    "question_length": 10,
    "answer_length": 50,
    "source_count": 3
}
```

### 推荐记录数据结构
```json
{
    "recommendation_id": "rec_1234567890",
    "user_id": "user123",
    "session_id": "session456",
    "requirement": "用户需求",
    "recommendation_text": "推荐内容",
    "products": ["推荐商品列表"],
    "timestamp": 1641024000,
    "created_at": "2022-01-01T12:00:00",
    "requirement_length": 20,
    "recommendation_length": 100,
    "product_count": 3
}
```

## ⚡ 性能优化建议

### 1. 批量操作
```python
# 批量获取多个用户的统计信息
users = ['user1', 'user2', 'user3']
stats_list = []
for user in users:
    stats = RAGConversationCache.get_conversation_statistics(user)
    stats_list.append(stats)
```

### 2. 分页查询
```python
# 分页获取大量历史记录
page_size = 20
page = 1

conversations = RAGConversationCache.get_user_conversations(
    user_id='user123',
    limit=page_size
)
```

### 3. 异步处理
```python
# 在视图中异步保存数据（可选）
import threading

def save_conversation_async(user_id, question, answer, sources):
    def _save():
        RAGConversationCache.save_conversation(
            user_id=user_id,
            question=question,
            answer=answer,
            sources=sources
        )
    
    thread = threading.Thread(target=_save)
    thread.start()
```

## 🚨 常见问题解决

### 1. Redis连接失败
```bash
# 检查Redis是否运行
redis-cli ping

# 如果返回PONG则正常，否则启动Redis
redis-server
```

### 2. 数据未保存
- 检查Redis配置中的数据库编号
- 确认过期时间设置是否合理
- 查看控制台错误日志

### 3. 性能问题
- 定期清理过期数据
- 监控Redis内存使用
- 合理设置最大记录数量

---

**提示**: 所有功能都有详细的错误处理，即使Redis不可用也不会影响核心业务功能！

