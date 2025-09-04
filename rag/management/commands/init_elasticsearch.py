"""
初始化Elasticsearch索引的Django管理命令
"""
from django.core.management.base import BaseCommand, CommandError
from rag.elasticsearch_service import es_service
from config import ELASTICSEARCH_CONFIG
import json


class Command(BaseCommand):
    help = '初始化Elasticsearch索引和映射'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild', 
            action='store_true',
            help='删除现有索引并重建'
        )
        parser.add_argument(
            '--index',
            type=str,
            help='指定要创建的索引名称 (products, knowledge, conversations)'
        )
    
    def handle(self, *args, **options):
        """执行命令"""
        if not es_service.is_available():
            self.stdout.write(
                self.style.WARNING('Elasticsearch服务不可用，跳过ES索引初始化')
            )
            self.stdout.write(
                self.style.SUCCESS('系统将使用ChromaDB作为向量存储后端')
            )
            return
        
        rebuild = options.get('rebuild', False)
        specific_index = options.get('index')
        
        # 索引配置定义
        index_configs = self._get_index_configs()
        
        # 处理指定索引
        if specific_index:
            if specific_index not in index_configs:
                raise CommandError(f'未知索引: {specific_index}')
            indices_to_create = {specific_index: index_configs[specific_index]}
        else:
            indices_to_create = index_configs
        
        # 创建索引
        for index_key, config in indices_to_create.items():
            index_name = ELASTICSEARCH_CONFIG['indices'][index_key]
            self._create_index(index_name, config, rebuild)
        
        self.stdout.write(
            self.style.SUCCESS('Elasticsearch索引初始化完成!')
        )
    
    def _get_index_configs(self):
        """获取索引配置"""
        return {
            'products': {
                'settings': {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "chinese_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "cjk_width"]
                            }
                        }
                    }
                },
                'mapping': {
                    "properties": {
                        "product_id": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "analyzer": "chinese_analyzer",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "brand": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "price": {"type": "float"},
                        "description": {
                            "type": "text",
                            "analyzer": "chinese_analyzer"
                        },
                        "attributes": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {"type": "text", "analyzer": "chinese_analyzer"}
                            }
                        },
                        "tags": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "indexed_at": {"type": "date"}
                    }
                }
            },
            'knowledge': {
                'settings': {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "chinese_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "cjk_width"]
                            }
                        }
                    }
                },
                'mapping': {
                    "properties": {
                        "knowledge_id": {"type": "keyword"},
                        "product_id": {"type": "keyword"},
                        "product_name": {
                            "type": "text", 
                            "analyzer": "chinese_analyzer"
                        },
                        "attribute": {"type": "keyword"},
                        "value": {
                            "type": "text",
                            "analyzer": "chinese_analyzer"
                        },
                        "source_text": {
                            "type": "text",
                            "analyzer": "chinese_analyzer"
                        },
                        "content_vector": {
                            "type": "dense_vector",
                            "dims": 768
                        },
                        "category": {"type": "keyword"},
                        "brand": {"type": "keyword"},
                        "confidence": {"type": "float"},
                        "created_at": {"type": "date"},
                        "indexed_at": {"type": "date"}
                    }
                }
            },
            'conversations': {
                'settings': {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "chinese_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "cjk_width"]
                            }
                        }
                    }
                },
                'mapping': {
                    "properties": {
                        "conversation_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        "question": {
                            "type": "text",
                            "analyzer": "chinese_analyzer",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "answer": {
                            "type": "text",
                            "analyzer": "chinese_analyzer"
                        },
                        "question_vector": {
                            "type": "dense_vector",
                            "dims": 768
                        },
                        "sources": {
                            "type": "nested",
                            "properties": {
                                "source": {"type": "text"},
                                "score": {"type": "float"},
                                "product_id": {"type": "keyword"}
                            }
                        },
                        "intent": {"type": "keyword"},
                        "satisfaction": {"type": "integer"},
                        "response_time": {"type": "integer"},
                        "created_at": {"type": "date"},
                        "indexed_at": {"type": "date"}
                    }
                }
            }
        }
    
    def _create_index(self, index_name, config, rebuild=False):
        """创建单个索引"""
        try:
            # 删除现有索引（如果需要重建）
            if rebuild:
                if es_service.delete_index(index_name):
                    self.stdout.write(f'已删除索引: {index_name}')
            
            # 创建索引
            if es_service.create_index(
                index_name=index_name,
                mapping=config['mapping'],
                settings=config['settings']
            ):
                self.stdout.write(
                    self.style.SUCCESS(f'索引创建成功: {index_name}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'索引创建失败: {index_name}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'创建索引 {index_name} 时发生错误: {e}')
            )

