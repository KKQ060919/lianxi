"""
Elasticsearch服务封装类
提供统一的搜索、索引和管理接口
"""
import logging
from typing import Dict, List, Any, Optional, Union
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError
from config import ELASTICSEARCH_CONFIG, SYSTEM_CONFIG
import json
import uuid
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

class ElasticsearchService:
    """Elasticsearch服务封装类"""
    
    def __init__(self):
        """初始化ES连接"""
        self.config = ELASTICSEARCH_CONFIG
        self.enabled = SYSTEM_CONFIG.get('use_elasticsearch', True)
        self.client = None
        
        if self.enabled:
            self._initialize_client()
    
    def _initialize_client(self):
        """初始化Elasticsearch客户端"""
        try:
            # 根据配置决定使用HTTP还是HTTPS
            scheme = self.config.get('scheme', 'http')
            
            # 构建连接URL
            if self.config.get('use_ssl', False):
                url = f"https://{self.config['host']}:{self.config['port']}"
                # 创建HTTPS配置
                self.client = Elasticsearch(
                    [url],
                    basic_auth=(self.config.get('username'), self.config.get('password')) if self.config.get('username') else None,
                    verify_certs=self.config.get('verify_certs', False),
                    ssl_show_warn=False,
                    timeout=self.config['timeout'],
                    max_retries=self.config['max_retries'],
                    retry_on_timeout=True
                )
            else:
                # HTTP配置（开发环境）
                url = f"http://{self.config['host']}:{self.config['port']}"
                self.client = Elasticsearch(
                    [url],
                    timeout=self.config['timeout'],
                    max_retries=self.config['max_retries'],
                    retry_on_timeout=True
                )
            
            # 测试连接
            if self.client.ping():
                logger.info("Elasticsearch连接成功")
                print("✅ Elasticsearch服务连接成功")
            else:
                logger.error("Elasticsearch连接失败")
                self.enabled = False
                
        except ConnectionError as e:
            logger.error(f"Elasticsearch连接失败: {e}")
            logger.info("正在尝试本地连接...")
            self._try_local_connection()
        except Exception as e:
            logger.error(f"初始化Elasticsearch客户端失败: {e}")
            self.enabled = False
            
    def _try_local_connection(self):
        """尝试连接本地Elasticsearch"""
        try:
            local_config = {
                'hosts': [{'host': 'localhost', 'port': 9200, 'scheme': 'http'}],
                'timeout': 10,
                'max_retries': 1,
                'retry_on_timeout': False
            }
            local_client = Elasticsearch(**local_config)
            if local_client.ping():
                logger.info("本地Elasticsearch连接成功，切换到本地模式")
                self.client = local_client
                self.config['host'] = 'localhost'
                return
        except Exception as e:
            logger.error(f"本地Elasticsearch连接也失败: {e}")
        
        logger.error("所有Elasticsearch连接尝试均失败，禁用ES功能")
        self.enabled = False
    
    def is_available(self) -> bool:
        """检查ES服务是否可用"""
        if not self.enabled or not self.client:
            return False
        try:
            return self.client.ping()
        except:
            return False
    
    def create_index(self, index_name: str, mapping: Dict, settings: Dict = None) -> bool:
        """创建索引"""
        if not self.is_available():
            return False
        
        try:
            # 默认设置
            default_settings = {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "chinese_analyzer": {
                            "type": "standard"
                        }
                    }
                }
            }
            
            if settings:
                default_settings.update(settings)
            
            # 检查索引是否存在
            if self.client.indices.exists(index=index_name):
                logger.info(f"索引 {index_name} 已存在")
                return True
            
            # 创建索引
            body = {
                "settings": default_settings,
                "mappings": mapping
            }
            
            self.client.indices.create(index=index_name, body=body)
            logger.info(f"索引 {index_name} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        """删除索引"""
        if not self.is_available():
            return False
        
        try:
            if self.client.indices.exists(index=index_name):
                self.client.indices.delete(index=index_name)
                logger.info(f"索引 {index_name} 删除成功")
                return True
            else:
                logger.info(f"索引 {index_name} 不存在")
                return True
                
        except Exception as e:
            logger.error(f"删除索引失败: {e}")
            return False
    
    def index_document(self, index_name: str, doc_id: str, document: Dict) -> bool:
        """索引单个文档"""
        if not self.is_available():
            return False
        
        try:
            # 添加时间戳
            document['indexed_at'] = datetime.now().isoformat()
            
            result = self.client.index(
                index=index_name,
                id=doc_id,
                document=document
            )
            
            logger.debug(f"文档索引成功: {doc_id}")
            return result['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"索引文档失败: {e}")
            return False
    
    def bulk_index_documents(self, index_name: str, documents: List[Dict]) -> Dict:
        """批量索引文档"""
        if not self.is_available():
            return {'success': False, 'error': 'ES不可用'}
        
        try:
            actions = []
            for doc in documents:
                # 生成文档ID（如果没有提供）
                doc_id = doc.get('id') or str(uuid.uuid4())
                
                # 添加时间戳
                doc_data = doc.copy()
                doc_data['indexed_at'] = datetime.now().isoformat()
                
                # ES bulk API格式：每个操作需要两行
                # 第一行：操作元数据
                action_meta = {
                    "index": {
                        "_index": index_name,
                        "_id": doc_id
                    }
                }
                actions.append(action_meta)
                # 第二行：文档数据
                actions.append(doc_data)
            
            # 批量操作
            result = self.client.bulk(body=actions)
            
            # 统计结果
            success_count = 0
            error_count = 0
            errors = []
            
            for item in result['items']:
                if 'index' in item:
                    if item['index'].get('status') in [200, 201]:
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(item['index'])
            
            logger.info(f"批量索引完成: 成功{success_count}, 失败{error_count}")
            
            return {
                'success': True,
                'total': len(documents),
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"批量索引失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def search_documents(self, index_name: str, query: Dict, size: int = 10, 
                        from_: int = 0, sort: List = None) -> Dict:
        """搜索文档"""
        if not self.is_available():
            return {'hits': [], 'total': 0, 'took': 0}
        
        try:
            body = {
                'query': query,
                'size': size,
                'from': from_
            }
            
            if sort:
                body['sort'] = sort
            
            result = self.client.search(index=index_name, body=body)
            
            # 格式化结果
            hits = []
            for hit in result['hits']['hits']:
                hits.append({
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source']
                })
            
            return {
                'hits': hits,
                'total': result['hits']['total']['value'],
                'took': result['took'],
                'max_score': result['hits']['max_score']
            }
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {'hits': [], 'total': 0, 'took': 0, 'error': str(e)}
    
    def multi_match_search(self, index_name: str, query_text: str, fields: List[str], 
                          size: int = 10, min_score: float = 0.1) -> Dict:
        """多字段匹配搜索"""
        search_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": fields,
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    }
                ],
                "filter": [
                    {
                        "range": {
                            "_score": {
                                "gte": min_score
                            }
                        }
                    }
                ]
            }
        }
        
        return self.search_documents(index_name, search_query, size=size)
    
    def semantic_search(self, index_name: str, vector: List[float], 
                       vector_field: str = "embedding", size: int = 10,
                       filter_query: Dict = None) -> Dict:
        """语义向量搜索"""
        try:
            # 使用正确的kNN搜索格式
            body = {
                "knn": {
                    "field": vector_field,
                    "query_vector": vector,
                    "k": size,
                    "num_candidates": size * 2
                },
                "size": size
            }
            
            # 如果有过滤条件，添加到查询中
            if filter_query:
                body["query"] = filter_query
            
            # 直接使用client.search而不是通过search_documents
            result = self.client.search(index=index_name, body=body)
            
            # 格式化结果
            hits = []
            for hit in result['hits']['hits']:
                hits.append({
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source']
                })
            
            return {
                'hits': hits,
                'total': result['hits']['total']['value'],
                'took': result['took'],
                'max_score': result['hits']['max_score']
            }
            
        except Exception as e:
            logger.warning(f"kNN搜索失败，回退到普通搜索: {e}")
            # 如果kNN不支持，回退到match_all查询
            fallback_query = filter_query or {"match_all": {}}
            return self.search_documents(index_name, fallback_query, size=size)
    
    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict]:
        """获取单个文档"""
        if not self.is_available():
            return None
        
        try:
            result = self.client.get(index=index_name, id=doc_id)
            return result['_source']
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            return None
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """删除文档"""
        if not self.is_available():
            return False
        
        try:
            self.client.delete(index=index_name, id=doc_id)
            logger.info(f"文档删除成功: {doc_id}")
            return True
        except NotFoundError:
            logger.info(f"文档不存在: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def count_documents(self, index_name: str, query: Dict = None) -> int:
        """统计文档数量"""
        if not self.is_available():
            return 0
        
        try:
            body = {'query': query} if query else None
            result = self.client.count(index=index_name, body=body)
            return result['count']
        except Exception as e:
            logger.error(f"统计文档失败: {e}")
            return 0

# 单例实例
es_service = ElasticsearchService()

