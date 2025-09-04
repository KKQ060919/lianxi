# Elasticsearch 集成说明

## 概述

本项目已成功集成Elasticsearch作为增强的RAG系统后端，提供更强大的搜索和知识检索功能。

## 新增功能

### 1. Elasticsearch服务封装
- 文件：`rag/elasticsearch_service.py`
- 提供统一的ES操作接口（索引、搜索、管理）
- 支持向量搜索和全文搜索

### 2. 增强RAG系统
- 文件：`rag/elasticsearch_rag.py`
- 基于ES的知识问答系统
- 结合语义搜索和关键词搜索
- 支持对话记录索引

### 3. 管理命令
- 文件：`rag/management/commands/init_elasticsearch.py`
- 初始化ES索引和映射
- 支持重建索引

### 4. API更新
- 智能选择RAG系统（ES优先，ChromaDB备选）
- 新增ES索引管理API
- 所有现有API都支持ES

## 配置

### Elasticsearch配置 (config.py)
```python
ELASTICSEARCH_CONFIG = {
    'host': '192.168.124.6',
    'port': 9200,
    'timeout': 30,
    'max_retries': 3,
    'use_ssl': False,
    'verify_certs': False,
    'indices': {
        'products': 'product_catalog',
        'knowledge': 'product_knowledge',
        'conversations': 'rag_conversations'
    }
}

SYSTEM_CONFIG = {
    'use_elasticsearch': True,  # 优先使用ES
}
```

## 使用方法

### 1. 初始化索引
```bash
# 创建所有索引
python manage.py init_elasticsearch

# 重建现有索引
python manage.py init_elasticsearch --rebuild

# 创建指定索引
python manage.py init_elasticsearch --index knowledge
```

### 2. API使用

#### 问答API (自动选择RAG系统)
```http
POST /api/rag/question/
Content-Type: application/json

{
    "question": "这个手机有什么特色功能？",
    "user_id": "user123",
    "session_id": "session456"
}
```

#### 初始化RAG系统
```http
POST /api/rag/initialize/
Content-Type: application/json

{
    "force_reload": true
}
```

#### 搜索知识库
```http
GET /api/rag/search/?query=手机&category=电子产品&size=10
```

#### ES索引管理
```http
# 获取索引状态
GET /api/rag/elasticsearch/index/

# 重建知识库索引
POST /api/rag/elasticsearch/index/
Content-Type: application/json

{
    "index_key": "knowledge",
    "force_rebuild": true
}
```

### 3. Python代码使用

```python
from rag.elasticsearch_rag import elasticsearch_rag_system
from rag.elasticsearch_service import es_service

# 检查ES可用性
if es_service.is_available():
    # 使用ES RAG系统
    result = elasticsearch_rag_system.ask_question("手机有什么功能？")
    print(result['answer'])

# 搜索知识库
results = elasticsearch_rag_system.search_knowledge(
    query="手机",
    filter_by_category="电子产品",
    size=5
)

# 更新知识
success = elasticsearch_rag_system.update_knowledge(
    product_id="PHONE001",
    attribute="电池容量",
    value="4000mAh",
    source_text="该手机配备4000mAh大电池"
)
```

## 系统架构

### 自动选择机制
系统会根据以下优先级选择RAG后端：
1. 如果ES可用且配置启用 → 使用Elasticsearch RAG
2. 否则 → 使用ChromaDB RAG

### 索引结构

#### 知识库索引 (product_knowledge)
- `product_id`: 商品ID
- `product_name`: 商品名称
- `attribute`: 属性名
- `value`: 属性值
- `content_vector`: 内容向量 (768维)
- `category`: 分类
- `brand`: 品牌

#### 对话索引 (rag_conversations)
- `conversation_id`: 对话ID
- `question`: 用户问题
- `answer`: 系统回答
- `question_vector`: 问题向量
- `sources`: 来源信息

## 优势

### 1. 性能优化
- 分布式搜索架构
- 并发处理能力强
- 支持大规模数据

### 2. 搜索增强
- 语义搜索 + 关键词搜索
- 智能结果合并
- 灵活的过滤条件

### 3. 可扩展性
- 易于添加新索引
- 支持集群部署
- 实时数据同步

### 4. 兼容性
- 无缝切换RAG后端
- 现有API完全兼容
- 渐进式升级

## 注意事项

1. **ES服务依赖**：需要确保Elasticsearch服务正常运行
2. **向量维度**：嵌入向量需要与配置的维度匹配（768维）
3. **内存使用**：ES会占用较多内存，建议合理配置
4. **数据同步**：修改数据库后需要重新索引到ES

## 故障排除

### ES连接问题
1. 检查ES服务是否运行
2. 验证网络连接和端口
3. 查看ES日志

### 索引问题
1. 使用管理命令重建索引
2. 检查映射配置
3. 验证数据格式

### 性能问题
1. 调整ES内存配置
2. 优化查询语句
3. 考虑分片设置

## 监控和维护

- 定期检查索引状态
- 监控查询性能
- 备份重要索引数据
- 根据需要调整配置

## 升级路径

如需禁用ES而使用ChromaDB：
```python
SYSTEM_CONFIG = {
    'use_elasticsearch': False,
}
```

系统会自动降级到ChromaDB模式，保证服务连续性。

