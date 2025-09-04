from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .RAG封装 import rag_system
from .elasticsearch_rag import elasticsearch_rag_system
from .elasticsearch_service import es_service
from .models import ProductKnowledge
from .redis import RAGConversationCache
from product.models import Products
from config import SYSTEM_CONFIG
import json
import uuid


def get_current_rag_system():
    """获取当前配置的RAG系统"""
    use_elasticsearch = SYSTEM_CONFIG.get('use_elasticsearch', True)
    
    if use_elasticsearch and es_service.is_available():
        return elasticsearch_rag_system, 'elasticsearch'
    else:
        return rag_system, 'chromadb'


class RAGQuestionView(APIView):
    """RAG问答API"""
    
    def post(self, request):
        """处理用户问题"""
        try:
            data = request.data
            question = data.get('question', '').strip()
            user_id = data.get('user_id', '')  # 获取用户ID（可选）
            session_id = data.get('session_id', '')  # 获取会话ID（匿名用户）
            
            # 参数验证
            if not question:
                return Response({
                    'code': 400,
                    'message': '问题不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取当前RAG系统
            current_rag_system, rag_type = get_current_rag_system()
            
            # 使用RAG系统获取答案
            result = current_rag_system.ask_question(question, return_source=True)
            
            if result['success']:
                # 生成对话ID
                conversation_id = str(uuid.uuid4())
                
                # 保存对话记录到Redis
                redis_conversation_id = RAGConversationCache.save_conversation(
                    user_id=user_id if user_id else None,
                    question=question,
                    answer=result['answer'],
                    sources=result['sources'],
                    session_id=session_id if session_id else None
                )
                
                # 如果使用ES，同时保存到ES中
                if rag_type == 'elasticsearch':
                    elasticsearch_rag_system.index_conversation(
                        conversation_id=conversation_id,
                        user_id=user_id or session_id or 'anonymous',
                        question=question,
                        answer=result['answer'],
                        sources=result['sources'],
                        session_id=session_id
                    )
                
                return Response({
                    'code': 200,
                    'message': '问答成功',
                    'data': {
                        'conversation_id': redis_conversation_id,  # 返回Redis对话ID
                        'question': question,
                        'answer': result['answer'],
                        'sources': result['sources'],
                        'total_sources': len(result['sources']),
                        'rag_type': rag_type  # 返回使用的RAG类型
                    }
                })
            else:
                # 即使失败也保存记录，便于分析问题
                conversation_id = RAGConversationCache.save_conversation(
                    user_id=user_id if user_id else None,
                    question=question,
                    answer=result['answer'],
                    sources=[],
                    session_id=session_id if session_id else None
                )
                
                return Response({
                    'code': 500,
                    'message': '问答处理失败',
                    'data': {
                        'conversation_id': conversation_id,
                        'question': question,
                        'answer': result['answer'],
                        'sources': [],
                        'rag_type': rag_type
                    }
                })
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RAGInitializeView(APIView):
    """RAG系统初始化API"""
    
    def post(self, request):
        """初始化或重新初始化RAG系统"""
        try:
            force_reload = request.data.get('force_reload', False)
            
            # 获取当前RAG系统
            current_rag_system, rag_type = get_current_rag_system()
            
            success = False
            message = ""
            
            if rag_type == 'elasticsearch':
                # 初始化Elasticsearch知识库索引
                success = elasticsearch_rag_system.index_product_knowledge(force_reload=force_reload)
                message = f'Elasticsearch RAG系统初始化{"成功" if success else "失败"}'
            else:
                # 初始化ChromaDB向量数据库
                success = rag_system.initialize_vector_store(force_reload=force_reload)
                message = f'ChromaDB RAG系统初始化{"成功" if success else "失败"}'
            
            if success:
                return Response({
                    'code': 200,
                    'message': message,
                    'data': {
                        'initialized': True,
                        'force_reload': force_reload,
                        'rag_type': rag_type
                    }
                })
            else:
                return Response({
                    'code': 500,
                    'message': message,
                    'data': {
                        'initialized': False,
                        'force_reload': force_reload,
                        'rag_type': rag_type
                    }
                })
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'初始化失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KnowledgeSearchView(APIView):
    """知识库搜索API"""
    
    def get(self, request):
        """搜索知识库内容"""
        try:
            query = request.GET.get('query', '').strip()
            category = request.GET.get('category', '')
            brand = request.GET.get('brand', '')
            size = int(request.GET.get('size', 10))
            
            if not query:
                return Response({
                    'code': 400,
                    'message': '搜索关键词不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取当前RAG系统
            current_rag_system, rag_type = get_current_rag_system()
            
            # 使用RAG系统搜索
            results = current_rag_system.search_knowledge(
                query=query,
                filter_by_category=category if category else None,
                filter_by_brand=brand if brand else None,
                size=size
            )
            
            return Response({
                'code': 200,
                'message': '搜索成功',
                'data': {
                    'query': query,
                    'filters': {
                        'category': category,
                        'brand': brand
                    },
                    'results': results,
                    'total_count': len(results),
                    'rag_type': rag_type
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'搜索失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductKnowledgeView(APIView):
    """商品知识管理API"""
    
    def get(self, request, product_id=None):
        """获取商品知识"""
        try:
            if product_id:
                # 获取指定商品的知识
                try:
                    product = Products.objects.get(product_id=product_id)
                    knowledge_items = ProductKnowledge.objects.filter(product=product)
                    
                    knowledge_data = []
                    for item in knowledge_items:
                        knowledge_data.append({
                            'id': item.id,
                            'attribute': item.attribute,
                            'value': item.value,
                            'source_text': item.source_text
                        })
                    
                    return Response({
                        'code': 200,
                        'message': '获取成功',
                        'data': {
                            'product_id': product_id,
                            'product_name': product.name,
                            'knowledge': knowledge_data,
                            'total_count': len(knowledge_data)
                        }
                    })
                    
                except Products.DoesNotExist:
                    return Response({
                        'code': 404,
                        'message': '商品不存在',
                        'data': None
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # 获取所有商品知识概览
                knowledge_items = ProductKnowledge.objects.select_related('product').all()[:50]
                
                knowledge_data = []
                for item in knowledge_items:
                    knowledge_data.append({
                        'id': item.id,
                        'product_id': item.product.product_id,
                        'product_name': item.product.name,
                        'brand': item.product.brand,
                        'category': item.product.category,
                        'attribute': item.attribute,
                        'value': item.value
                    })
                
                return Response({
                    'code': 200,
                    'message': '获取成功',
                    'data': {
                        'knowledge': knowledge_data,
                        'total_count': len(knowledge_data)
                    }
                })
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """添加商品知识"""
        try:
            data = request.data
            product_id = data.get('product_id')
            attribute = data.get('attribute')
            value = data.get('value')
            source_text = data.get('source_text', '')
            
            # 参数验证
            if not all([product_id, attribute, value]):
                return Response({
                    'code': 400,
                    'message': '商品ID、属性名和属性值不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取当前RAG系统
            current_rag_system, rag_type = get_current_rag_system()
            
            # 更新知识库
            success = current_rag_system.update_knowledge(
                product_id=product_id,
                attribute=attribute,
                value=value,
                source_text=source_text
            )
            
            if success:
                return Response({
                    'code': 200,
                    'message': '知识添加成功',
                    'data': {
                        'product_id': product_id,
                        'attribute': attribute,
                        'value': value,
                        'rag_type': rag_type
                    }
                })
            else:
                return Response({
                    'code': 500,
                    'message': '知识添加失败',
                    'data': {'rag_type': rag_type}
                })
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'添加失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SimilarQuestionsView(APIView):
    """相似问题推荐API"""
    
    def get(self, request):
        """获取相似问题"""
        try:
            question = request.GET.get('question', '').strip()
            limit = int(request.GET.get('limit', 5))
            
            if not question:
                return Response({
                    'code': 400,
                    'message': '问题不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取当前RAG系统
            current_rag_system, rag_type = get_current_rag_system()
            
            # 获取相似问题
            similar_questions = current_rag_system.get_similar_questions(question, limit)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'original_question': question,
                    'similar_questions': similar_questions,
                    'count': len(similar_questions),
                    'rag_type': rag_type
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ElasticsearchIndexView(APIView):
    """Elasticsearch索引管理API"""
    
    def get(self, request):
        """获取ES索引状态"""
        try:
            if not es_service.is_available():
                return Response({
                    'code': 503,
                    'message': 'Elasticsearch服务不可用',
                    'data': {
                        'available': False,
                        'indices': {}
                    }
                })
            
            indices_status = {}
            for index_key, index_name in es_service.config['indices'].items():
                doc_count = es_service.count_documents(index_name)
                indices_status[index_key] = {
                    'name': index_name,
                    'document_count': doc_count,
                    'exists': doc_count >= 0
                }
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'available': True,
                    'indices': indices_status
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取索引状态失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """重建指定索引"""
        try:
            data = request.data
            index_key = data.get('index_key')  # products, knowledge, conversations
            force_rebuild = data.get('force_rebuild', False)
            
            if not es_service.is_available():
                return Response({
                    'code': 503,
                    'message': 'Elasticsearch服务不可用',
                    'data': None
                })
            
            if not index_key:
                # 重建所有知识库索引
                success = elasticsearch_rag_system.index_product_knowledge(force_reload=force_rebuild)
                message = f'知识库索引重建{"成功" if success else "失败"}'
                
                return Response({
                    'code': 200 if success else 500,
                    'message': message,
                    'data': {
                        'rebuilt': success,
                        'index_key': 'knowledge',
                        'force_rebuild': force_rebuild
                    }
                })
            elif index_key == 'knowledge':
                success = elasticsearch_rag_system.index_product_knowledge(force_reload=force_rebuild)
                message = f'知识库索引重建{"成功" if success else "失败"}'
            else:
                return Response({
                    'code': 400,
                    'message': f'不支持的索引类型: {index_key}',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({
                'code': 200 if success else 500,
                'message': message,
                'data': {
                    'rebuilt': success,
                    'index_key': index_key,
                    'force_rebuild': force_rebuild
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'重建索引失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationHistoryView(APIView):
    """对话历史管理API"""
    
    def get(self, request):
        """获取用户对话历史"""
        try:
            user_id = request.GET.get('user_id', '')
            session_id = request.GET.get('session_id', '')
            limit = int(request.GET.get('limit', 20))
            
            # 获取对话历史
            conversations = RAGConversationCache.get_user_conversations(
                user_id=user_id if user_id else None,
                session_id=session_id if session_id else None,
                limit=limit
            )
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'conversations': conversations,
                    'total_count': len(conversations),
                    'user_id': user_id or session_id or 'anonymous'
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取对话历史失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """删除指定对话记录"""
        try:
            data = request.data
            conversation_id = data.get('conversation_id')
            user_id = data.get('user_id', '')
            session_id = data.get('session_id', '')
            
            if not conversation_id:
                return Response({
                    'code': 400,
                    'message': '对话ID不能为空',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 删除对话记录
            success = RAGConversationCache.delete_conversation(
                conversation_id=conversation_id,
                user_id=user_id if user_id else None,
                session_id=session_id if session_id else None
            )
            
            if success:
                return Response({
                    'code': 200,
                    'message': '对话记录删除成功',
                    'data': {
                        'conversation_id': conversation_id
                    }
                })
            else:
                return Response({
                    'code': 404,
                    'message': '对话记录不存在或删除失败',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'删除对话记录失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PopularQuestionsView(APIView):
    """热门问题API"""
    
    def get(self, request):
        """获取热门问题列表"""
        try:
            limit = int(request.GET.get('limit', 10))
            
            popular_questions = RAGConversationCache.get_popular_questions(limit)
            
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': {
                    'popular_questions': popular_questions,
                    'total_count': len(popular_questions)
                }
            })
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'获取热门问题失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)