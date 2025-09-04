from django.urls import path
from .views import (
    RAGQuestionView,
    RAGInitializeView,
    KnowledgeSearchView,
    ProductKnowledgeView,
    SimilarQuestionsView,
    ConversationHistoryView,
    PopularQuestionsView,
    ElasticsearchIndexView
)

app_name = 'rag'

urlpatterns = [
    # RAG问答
    path('question/', RAGQuestionView.as_view(), name='rag_question'),
    
    # RAG系统初始化
    path('initialize/', RAGInitializeView.as_view(), name='rag_initialize'),
    
    # 知识库搜索
    path('search/', KnowledgeSearchView.as_view(), name='knowledge_search'),
    
    # 商品知识管理
    path('knowledge/', ProductKnowledgeView.as_view(), name='product_knowledge_list'),
    path('knowledge/<str:product_id>/', ProductKnowledgeView.as_view(), name='product_knowledge_detail'),
    
    # 相似问题推荐
    path('similar-questions/', SimilarQuestionsView.as_view(), name='similar_questions'),
    
    # 对话历史管理
    path('conversations/', ConversationHistoryView.as_view(), name='conversation_history'),
    
    # 热门问题
    path('popular-questions/', PopularQuestionsView.as_view(), name='popular_questions'),
    
    # Elasticsearch索引管理
    path('elasticsearch/index/', ElasticsearchIndexView.as_view(), name='elasticsearch_index'),
]