# Redis功能集成说明

本项目已成功集成Redis缓存功能，实现RAG对话和智能推荐的存储与管理。

## 🔧 功能概述

### 1. RAG对话存储功能
- **对话记录存储**: 自动保存用户问题、AI回答、知识来源等信息
- **对话历史管理**: 支持获取、搜索、删除用户对话记录
- **热门问题统计**: 自动统计用户常见问题，便于优化服务
- **对话数据分析**: 提供对话统计信息，包括字符数、来源数量等

### 2. 智能推荐存储功能
- **推荐记录存储**: 保存用户需求、推荐内容、推荐商品信息
- **推荐历史管理**: 支持获取、搜索、删除用户推荐记录  
- **用户偏好管理**: 存储和管理用户偏好设置
- **热门需求分析**: 统计用户常见需求，辅助产品规划
- **推荐效果统计**: 提供全局和用户维度的推荐统计数据

## 📁 文件结构

```
项目根目录/
├── config.py                          # 新增Redis配置
├── rag/
│   ├── redis.py                       # RAG对话缓存管理类 (新增)
│   ├── views.py                       # 更新：增加Redis存储功能
│   └── urls.py                        # 更新：增加新API路由
├── Agents/
│   ├── redis.py                       # 智能推荐缓存管理类 (新增)
│   ├── views.py                       # 更新：增加Redis存储功能
│   └── urls.py                        # 更新：增加新API路由
├── test_redis_integration.py          # Redis功能测试脚本 (新增)
└── README_Redis功能说明.md            # 本说明文档 (新增)
```

## ⚙️ 配置说明

### Redis配置 (config.py)
```python
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'rag_db': 2,      # RAG对话存储数据库
    'agents_db': 3,   # 智能推荐存储数据库
    'default_expire': 7 * 24 * 3600,  # 默认过期时间：7天
    'max_conversations': 50,  # 每个用户最多保存的对话数量
    'max_recommendations': 20,  # 每个用户最多保存的推荐记录数量
}
```

### Redis数据库分配
- **数据库0**: 商品缓存 (product/redis.py)
- **数据库1**: 用户行为缓存 (users/redis.py)
- **数据库2**: RAG对话存储 (rag/redis.py)
- **数据库3**: 智能推荐存储 (Agents/redis.py)

## 🚀 新增API接口

### RAG相关API

#### 1. RAG问答 (更新)
- **URL**: `POST /rag/question/`
- **功能**: 原有问答功能 + 自动保存对话记录
- **新增字段**:
  - `user_id` (可选): 用户ID
  - `session_id` (可选): 会话ID (匿名用户)
- **返回**: 新增 `conversation_id` 字段

#### 2. 对话历史管理 (新增)
- **URL**: `GET /rag/conversations/`
- **功能**: 获取用户对话历史
- **参数**: 
  - `user_id` (可选): 用户ID
  - `session_id` (可选): 会话ID
  - `limit` (可选): 返回数量，默认20

- **URL**: `DELETE /rag/conversations/`
- **功能**: 删除指定对话记录
- **参数**: `conversation_id`, `user_id`, `session_id`

#### 3. 热门问题 (新增)
- **URL**: `GET /rag/popular-questions/`
- **功能**: 获取热门问题列表
- **参数**: `limit` (可选): 返回数量，默认10

### 智能推荐相关API

#### 1. 智能推荐 (更新)
- **URL**: `POST /agents/recommend/`
- **功能**: 原有推荐功能 + 自动保存推荐记录
- **新增字段**:
  - `session_id` (可选): 会话ID (匿名用户)
- **返回**: 新增 `recommendation_id` 字段

#### 2. 推荐历史管理 (新增)
- **URL**: `GET /agents/history/`
- **功能**: 获取用户推荐历史
- **参数**:
  - `user_id` (可选): 用户ID
  - `session_id` (可选): 会话ID
  - `limit` (可选): 返回数量，默认20

- **URL**: `DELETE /agents/history/`
- **功能**: 删除指定推荐记录
- **参数**: `recommendation_id`, `user_id`, `session_id`

#### 3. 热门需求 (新增)
- **URL**: `GET /agents/popular-requirements/`
- **功能**: 获取热门需求列表
- **参数**: `limit` (可选): 返回数量，默认10

## 🔍 核心类说明

### RAGConversationCache (rag/redis.py)
```python
# 主要方法
- save_conversation()          # 保存对话记录
- get_conversation_detail()    # 获取对话详情
- get_user_conversations()     # 获取用户对话历史
- get_popular_questions()      # 获取热门问题
- get_conversation_statistics() # 获取对话统计
- delete_conversation()        # 删除对话记录
- search_conversations()       # 搜索对话记录
```

### RecommendationCache (Agents/redis.py)
```python
# 主要方法
- save_recommendation()              # 保存推荐记录
- get_recommendation_detail()        # 获取推荐详情
- get_user_recommendations()         # 获取用户推荐历史
- save_user_preferences()            # 保存用户偏好
- get_user_preferences()             # 获取用户偏好
- get_popular_requirements()         # 获取热门需求
- get_recommendation_stats()         # 获取推荐统计
- delete_recommendation()            # 删除推荐记录
```

## 🧪 测试方法

### 1. 运行集成测试
```bash
python test_redis_integration.py
```

### 2. 测试内容
- Redis连接测试
- RAG对话存储功能测试
- 智能推荐存储功能测试
- 数据一致性验证
- 性能基准测试

### 3. 手动API测试

#### RAG对话测试
```bash
# 发送问题
curl -X POST http://localhost:8000/rag/question/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "iPhone 15有什么特点？",
    "user_id": "test_user",
    "session_id": "session_123"
  }'

# 获取对话历史
curl -X GET "http://localhost:8000/rag/conversations/?user_id=test_user&limit=10"

# 获取热门问题
curl -X GET "http://localhost:8000/rag/popular-questions/?limit=5"
```

#### 智能推荐测试
```bash
# 获取推荐
curl -X POST http://localhost:8000/agents/recommend/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "requirement": "推荐性价比高的手机",
    "session_id": "session_123"
  }'

# 获取推荐历史
curl -X GET "http://localhost:8000/agents/history/?user_id=test_user&limit=10"

# 获取热门需求
curl -X GET "http://localhost:8000/agents/popular-requirements/?limit=5"
```

## 💡 使用建议

### 1. 数据过期策略
- 对话记录默认保存7天，可根据业务需求调整
- 热门问题保存30天，用于长期趋势分析
- 用户偏好长期保存，直到用户更新

### 2. 性能优化
- 使用Redis的ZSET数据结构确保时间序列排序
- 自动清理超出限制的历史记录
- 支持分页查询，避免大数据量响应

### 3. 扩展建议
- 可添加对话标签功能，便于分类管理
- 可实现推荐效果反馈机制
- 可添加用户行为分析功能

## 🚨 注意事项

1. **Redis服务**: 确保Redis服务正在运行
2. **数据库分离**: 不同功能使用不同数据库，避免键名冲突
3. **错误处理**: 所有Redis操作都有异常捕获，不会影响主业务流程
4. **匿名用户**: 支持通过session_id跟踪匿名用户的对话和推荐
5. **数据清理**: 定期清理过期数据，保持Redis性能

## 📈 监控建议

- 监控Redis内存使用情况
- 跟踪API响应时间
- 统计对话和推荐的成功率
- 定期备份重要的用户偏好数据

---

**开发完成时间**: 2024年12月
**版本**: 1.0
**状态**: 生产就绪 ✅

