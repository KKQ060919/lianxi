"""
基于Elasticsearch的增强RAG系统
集成向量搜索和全文搜索功能
"""
import logging
from typing import Dict, List, Any, Optional
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import uuid
from datetime import datetime

from .elasticsearch_service import es_service
from .models import ProductKnowledge
from product.models import Products
from config import API_CONFIG, RAG_CONFIG, ELASTICSEARCH_CONFIG

# 配置日志
logger = logging.getLogger(__name__)

class ElasticsearchRAGSystem:
    """基于Elasticsearch的RAG系统"""
    
    def __init__(self):
        """初始化RAG系统"""
        # 初始化大语言模型
        self.llm = ChatOpenAI(
            api_key=API_CONFIG['qwen_api_key'],
            base_url=API_CONFIG['qwen_base_url'],
            model=API_CONFIG['qwen_model']
        )
        
        # 初始化嵌入模型
        self.embeddings_model = DashScopeEmbeddings(
            model=API_CONFIG['embedding_model'],
            dashscope_api_key=API_CONFIG['embedding_api_key']
        )
        
        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAG_CONFIG['chunk_size'],
            chunk_overlap=RAG_CONFIG['chunk_overlap']
        )
        
        # 索引配置
        self.indices = ELASTICSEARCH_CONFIG['indices']
        
        # 提示模板
        self.prompt_template = PromptTemplate.from_template("""
你是一个专业的商品知识问答助手。请根据以下检索到的知识库信息，准确回答用户问题。

检索到的相关信息：
{context}

用户问题：{question}

回答要求：
1. 基于知识库信息进行准确回答
2. 如果信息不足，明确说明
3. 回答要具体、有用
4. 保持专业和友好的语调

回答：""")
        
        # 创建RAG链
        self.rag_chain = None
        self._setup_rag_chain()
    
    def _setup_rag_chain(self):
        """设置RAG链"""
        try:
            # 创建检索器
            def retriever_func(question: str) -> str:
                return self._retrieve_context(question)
            
            # 创建RAG链
            self.rag_chain = (
                {"context": retriever_func, "question": lambda x: x} 
                | self.prompt_template 
                | self.llm 
                | StrOutputParser()
            )
            
            logger.info("RAG链设置成功")
            
        except Exception as e:
            logger.error(f"设置RAG链失败: {e}")
    
    def _retrieve_context(self, question: str, top_k: int = 5) -> str:
        """检索相关上下文"""
        try:
            # 生成问题向量
            question_vector = self.embeddings_model.embed_query(question)
            
            # 1. 向量搜索（语义相似度）
            semantic_results = es_service.semantic_search(
                index_name=self.indices['knowledge'],
                vector=question_vector,
                vector_field="content_vector",
                size=top_k
            )
            
            # 2. 全文搜索（关键词匹配）
            text_results = es_service.multi_match_search(
                index_name=self.indices['knowledge'],
                query_text=question,
                fields=['value^2', 'source_text', 'product_name'],
                size=top_k
            )
            
            # 合并和去重结果
            all_results = self._merge_search_results(
                semantic_results['hits'], 
                text_results['hits']
            )
            
            # 构建上下文
            context_parts = []
            for i, result in enumerate(all_results[:top_k]):
                source = result['source']
                context_parts.append(
                    f"知识{i+1}：商品：{source.get('product_name', 'N/A')} "
                    f"| 属性：{source.get('attribute', 'N/A')} "
                    f"| 内容：{source.get('value', 'N/A')}"
                )
            
            return "\n".join(context_parts) if context_parts else "未找到相关信息"
            
        except Exception as e:
            logger.error(f"检索上下文失败: {e}")
            return "检索失败"
    
    def _merge_search_results(self, semantic_results: List, text_results: List) -> List:
        """合并搜索结果并去重"""
        merged = {}
        
        # 处理语义搜索结果（权重更高）
        for result in semantic_results:
            doc_id = result['id']
            merged[doc_id] = {
                'id': doc_id,
                'score': result['score'] * 1.2,  # 语义搜索权重稍高
                'source': result['source'],
                'type': 'semantic'
            }
        
        # 处理文本搜索结果
        for result in text_results:
            doc_id = result['id']
            if doc_id in merged:
                # 结合分数
                merged[doc_id]['score'] = max(
                    merged[doc_id]['score'], 
                    result['score']
                )
                merged[doc_id]['type'] = 'hybrid'
            else:
                merged[doc_id] = {
                    'id': doc_id,
                    'score': result['score'],
                    'source': result['source'],
                    'type': 'text'
                }
        
        # 按分数排序
        sorted_results = sorted(
            merged.values(), 
            key=lambda x: x['score'], 
            reverse=True
        )
        
        return sorted_results
    
    def ask_question(self, question: str, return_source: bool = False) -> Dict:
        """处理用户问题"""
        try:
            if not es_service.is_available():
                return {
                    'success': False,
                    'answer': 'Elasticsearch服务不可用，无法处理问题',
                    'sources': []
                }
            
            # 使用RAG链生成回答
            answer = self.rag_chain.invoke(question)
            
            # 获取源文档（如果需要）
            sources = []
            if return_source:
                # 重新检索获取源信息
                question_vector = self.embeddings_model.embed_query(question)
                search_results = es_service.semantic_search(
                    index_name=self.indices['knowledge'],
                    vector=question_vector,
                    vector_field="content_vector",
                    size=3
                )
                
                for result in search_results['hits']:
                    source_data = result['source']
                    sources.append({
                        'source': f"{source_data.get('product_name', 'N/A')} - {source_data.get('attribute', 'N/A')}",
                        'content': source_data.get('value', 'N/A'),
                        'score': result['score'],
                        'metadata': {
                            'product_name': source_data.get('product_name', 'N/A'),
                            'brand': source_data.get('brand', 'N/A'),
                            'category': source_data.get('parent_category', 'N/A'),
                            'attribute': source_data.get('attribute', 'N/A'),
                            'product_id': source_data.get('product_id', 'N/A')
                        }
                    })
            
            return {
                'success': True,
                'answer': answer,
                'sources': sources
            }
            
        except Exception as e:
            logger.error(f"问答处理失败: {e}")
            return {
                'success': False,
                'answer': f'处理问题时发生错误: {str(e)}',
                'sources': []
            }
    
    def search_knowledge(self, query: str, filter_by_category: str = None, 
                        filter_by_brand: str = None, size: int = 10) -> List[Dict]:
        """搜索知识库"""
        try:
            if not es_service.is_available():
                return []
            
            # 构建搜索查询
            search_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["value^2", "source_text", "product_name"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            }
            
            # 添加过滤条件
            filters = []
            if filter_by_category:
                filters.append({"term": {"category": filter_by_category}})
            if filter_by_brand:
                filters.append({"term": {"brand": filter_by_brand}})
            
            if filters:
                search_query["bool"]["filter"] = filters
            
            # 执行搜索
            results = es_service.search_documents(
                index_name=self.indices['knowledge'],
                query=search_query,
                size=size
            )
            
            # 格式化结果
            formatted_results = []
            for hit in results['hits']:
                source = hit['source']
                formatted_results.append({
                    'id': hit['id'],
                    'product_id': source.get('product_id', 'N/A'),
                    'product_name': source.get('product_name', 'N/A'),
                    'brand': source.get('brand', 'N/A'),
                    'category': source.get('category', 'N/A'),
                    'attribute': source.get('attribute', 'N/A'),
                    'value': source.get('value', 'N/A'),
                    'score': hit['score']
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return []
    
    def index_product_knowledge(self, force_reload: bool = False) -> bool:
        """索引商品知识到Elasticsearch"""
        try:
            if not es_service.is_available():
                logger.error("Elasticsearch不可用")
                return False
            
            # 获取所有商品知识
            knowledge_items = ProductKnowledge.objects.select_related('product').all()
            
            if not knowledge_items.exists():
                logger.info("没有找到商品知识数据")
                return True
            
            # 批量索引文档
            documents = []
            for item in knowledge_items:
                # 生成内容向量
                content_text = f"{item.attribute} {item.value} {item.source_text}"
                content_vector = self.embeddings_model.embed_query(content_text)
                
                doc = {
                    'id': f"knowledge_{item.id}",
                    'knowledge_id': item.id,
                    'product_id': item.product.product_id,
                    'product_name': item.product.name,
                    'brand': item.product.brand,
                    'category': item.product.category,
                    'attribute': item.attribute,
                    'value': item.value,
                    'source_text': item.source_text,
                    'content_vector': content_vector,
                    'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else None
                }
                documents.append(doc)
            
            # 批量索引
            result = es_service.bulk_index_documents(
                index_name=self.indices['knowledge'],
                documents=documents
            )
            
            if result['success']:
                logger.info(f"成功索引 {result['success_count']} 条知识记录")
                return True
            else:
                logger.error(f"索引失败: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"索引商品知识失败: {e}")
            return False
    
    def update_knowledge(self, product_id: str, attribute: str, value: str, source_text: str = "") -> bool:
        """更新知识库"""
        try:
            # 更新数据库
            product = Products.objects.get(product_id=product_id)
            knowledge_item, created = ProductKnowledge.objects.get_or_create(
                product=product,
                attribute=attribute,
                defaults={
                    'value': value,
                    'source_text': source_text
                }
            )
            
            if not created:
                knowledge_item.value = value
                knowledge_item.source_text = source_text
                knowledge_item.save()
            
            # 更新Elasticsearch索引
            if es_service.is_available():
                content_text = f"{attribute} {value} {source_text}"
                content_vector = self.embeddings_model.embed_query(content_text)
                
                doc = {
                    'knowledge_id': knowledge_item.id,
                    'product_id': product_id,
                    'product_name': product.name,
                    'brand': product.brand,
                    'category': product.category,
                    'attribute': attribute,
                    'value': value,
                    'source_text': source_text,
                    'content_vector': content_vector,
                    'created_at': datetime.now().isoformat()
                }
                
                es_service.index_document(
                    index_name=self.indices['knowledge'],
                    doc_id=f"knowledge_{knowledge_item.id}",
                    document=doc
                )
            
            return True
            
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
            return False
    
    def get_similar_questions(self, question: str, limit: int = 5) -> List[str]:
        """获取相似问题"""
        try:
            if not es_service.is_available():
                return []
            
            # 生成问题向量
            question_vector = self.embeddings_model.embed_query(question)
            
            # 在对话索引中搜索相似问题
            results = es_service.semantic_search(
                index_name=self.indices['conversations'],
                vector=question_vector,
                vector_field="question_vector",
                size=limit * 2  # 获取更多结果用于去重
            )
            
            # 提取相似问题并去重
            similar_questions = []
            seen_questions = set()
            
            for result in results['hits']:
                source = result['source']
                question_text = source.get('question', '').strip()
                
                if (question_text and 
                    question_text not in seen_questions and 
                    question_text != question and
                    len(similar_questions) < limit):
                    
                    similar_questions.append(question_text)
                    seen_questions.add(question_text)
            
            return similar_questions
            
        except Exception as e:
            logger.error(f"获取相似问题失败: {e}")
            return []
    
    def index_conversation(self, conversation_id: str, user_id: str, question: str, 
                          answer: str, sources: List[Dict], session_id: str = None) -> bool:
        """索引对话记录"""
        try:
            if not es_service.is_available():
                return False
            
            # 生成问题向量
            question_vector = self.embeddings_model.embed_query(question)
            
            doc = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'session_id': session_id,
                'question': question,
                'answer': answer,
                'question_vector': question_vector,
                'sources': sources,
                'created_at': datetime.now().isoformat()
            }
            
            return es_service.index_document(
                index_name=self.indices['conversations'],
                doc_id=conversation_id,
                document=doc
            )
            
        except Exception as e:
            logger.error(f"索引对话失败: {e}")
            return False

# 创建全局实例
elasticsearch_rag_system = ElasticsearchRAGSystem()

