"""
系统配置文件
集中管理所有配置项，避免硬编码
"""
import os

# API配置
API_CONFIG = {
    # 阿里云通义千问配置
    'qwen_api_key': "sk-5e387f862dd94499955b83ffe78c722c",
    'qwen_base_url': "https://dashscope.aliyuncs.com/compatible-mode/v1",
    'qwen_model': "qwen-max",
    
    # DashScope嵌入模型配置
    'embedding_api_key': "sk-8869c2ac51c5466185e6e39faefff6db",
    'embedding_model': "text-embedding-v3",
}

# Agent配置
AGENT_CONFIG = {
    'max_iterations': 10,  # 增加最大迭代次数
    'handle_parsing_errors': True,
    'verbose': False,  # 减少日志输出
}

# RAG配置
RAG_CONFIG = {
    'chunk_size': 500,
    'chunk_overlap': 100,
    'retriever_k': 5,
    'vector_store_path': "./chroma_product_knowledge",
    'enable_external_db': False,  # 默认禁用外部数据库
}

# 数据库配置
DATABASE_CONFIG = {
    'external_mysql': {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'book_rag_knowledge_base',
        'charset': 'utf8mb4',
    }
}

# API端点配置
API_ENDPOINTS = {
    'base_url': "http://localhost:8000",
    'timeout': 30,
}

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'rag_db': 2,      # RAG对话存储数据库
    'agents_db': 3,   # 智能推荐存储数据库
    'default_expire': 7 * 24 * 3600,  # 默认过期时间：7天
    'max_conversations': 50,  # 每个用户最多保存的对话数量
    'max_recommendations': 20,  # 每个用户最多保存的推荐记录数量
}

# Elasticsearch配置
ELASTICSEARCH_CONFIG = {
    'host': 'localhost',
    'port': 9200,
    'use_ssl': True,  # 启用SSL，使用HTTPS
    'verify_certs': False,
    'scheme': 'https',  # 使用HTTPS协议
    'timeout': 30,
    'max_retries': 3,
    'username': 'elastic',  # ES用户名
    'password': 'waQI9i90sqBerrslok*A',  # ES密码
    'indices': {
        'products': 'rag_products_index',
        'knowledge': 'rag_knowledge_index',
        'conversations': 'rag_conversations_index'
    }
}

# 系统配置
SYSTEM_CONFIG = {
    'max_history_records': 10,
    'max_recommendation_sources': 3,
    'enable_debug': False,
    'use_elasticsearch': True,  # 启用Elasticsearch
}

