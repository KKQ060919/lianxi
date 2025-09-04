from operator import itemgetter
import pymysql
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .models import ProductKnowledge
from product.models import Products
import json
import os

class ProductRAGSystem:
    """商品知识问答RAG系统"""
    
    def __init__(self):
        """初始化RAG系统"""
        # 初始化大语言模型
        self.llm = ChatOpenAI(
            api_key="sk-5e387f862dd94499955b83ffe78c722c",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-max"
        )
        
        # 初始化文本嵌入模型
        self.embeddings_model = DashScopeEmbeddings(
            model="text-embedding-v3",
            dashscope_api_key="sk-8869c2ac51c5466185e6e39faefff6db"
        )
        
        # 定义文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, 
            chunk_overlap=100
        )
        
        # 初始化Chroma向量存储
        self.vector_store = None
        self.retriever = None
        self._setup_vector_store()
        
        # 定义提示模板
        self.prompt_template = PromptTemplate.from_template("""
            你是一个专业的商品知识问答助手，根据以下商品知识库信息回答用户问题：

            知识库信息：
            {context}

            用户问题：{question}

            请根据提供的知识库信息准确回答问题。如果知识库中没有相关信息，请如实说明。
            回答时请保持专业、准确、有帮助的语调。
        """)
        
        # 构建RAG处理链
        self.chain = (
            {"question": RunnablePassthrough()}
            | RunnablePassthrough.assign(context=itemgetter("question") | self.retriever)
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )
        
        # 初始化向量数据库标志
        self.is_initialized = False
    
    def _setup_vector_store(self):
        """设置向量存储"""
        try:
            self.vector_store = Chroma(
                embedding_function=self.embeddings_model, 
                persist_directory="./chroma_product_knowledge",
                collection_name="product_knowledge"
            )
            
            # 检查collection是否存在，如果不存在则创建
            try:
                # 尝试获取collection信息
                self.vector_store.get()
                print("ChromaDB向量存储连接成功")
            except Exception as e:
                print(f"ChromaDB向量存储需要初始化: {str(e)}")
                # 重新创建collection
                self.vector_store = Chroma(
                    embedding_function=self.embeddings_model, 
                    persist_directory="./chroma_product_knowledge",
                    collection_name="product_knowledge"
                )
            
            # 创建检索器
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
            
        except Exception as e:
            print(f"设置ChromaDB向量存储失败: {str(e)}")
            self.vector_store = None
            self.retriever = None
    
    def load_product_knowledge_from_db(self):
        """从数据库加载商品知识"""
        try:
            documents = []
            
            # 从ProductKnowledge模型获取数据
            knowledge_items = ProductKnowledge.objects.select_related('product').all()
            
            for item in knowledge_items:
                # 构建文档内容
                content = f"""
                商品名称: {item.product.name}
                商品品牌: {item.product.brand}
                商品分类: {item.product.category}
                属性: {item.attribute}
                属性值: {item.value}
                详细描述: {item.source_text or ''}
                """
                
                # 创建Document对象
                doc = Document(
                    page_content=content.strip(),
                    metadata={
                        'product_id': item.product.product_id,
                        'product_name': item.product.name,
                        'brand': item.product.brand,
                        'category': item.product.category,
                        'attribute': item.attribute,
                        'knowledge_id': item.id
                    }
                )
                documents.append(doc)
            
            print(f"从数据库加载了 {len(documents)} 个商品知识文档")
            return documents
            
        except Exception as e:
            print(f"从数据库加载商品知识失败: {str(e)}")
            return []
    
    def load_knowledge_from_mysql(self):
        """从MySQL外部知识库加载数据（兼容原有脚本）"""
        try:
            # 连接外部知识库数据库
            connection = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                password='123456',
                database='book_rag_knowledge_base',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            documents = []

            with connection.cursor() as cursor:
                # 查询知识内容
                sql = """
                SELECT 
                    c.content_detail,
                    cat.parent_category,
                    cat.child_category
                FROM book_knowledge_content c
                LEFT JOIN book_knowledge_category cat ON c.category_id = cat.category_id
                """

                cursor.execute(sql)
                results = cursor.fetchall()

                for row in results:
                    if row['content_detail']:
                        doc = Document(
                            page_content=row['content_detail'],
                            metadata={
                                'parent_category': row['parent_category'] or "未分类",
                                'child_category': row['child_category'] or "未分类",
                                'source': 'external_knowledge_base'
                            }
                        )
                        documents.append(doc)

            connection.close()
            print(f"从外部MySQL知识库加载了 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            print(f"从外部MySQL知识库加载失败: {str(e)}")
            return []
    
    def initialize_vector_store(self, force_reload=False):
        """初始化向量数据库"""
        try:
            # 检查是否需要重新加载
            if self.is_initialized and not force_reload and self.vector_store is not None:
                print("向量数据库已初始化")
                return True
            
            # 如果强制重新加载，清空现有数据
            if force_reload or self.vector_store is None:
                print("重新设置向量存储...")
                # 重新设置向量存储
                self._setup_vector_store()
                
                if self.vector_store is None:
                    print("向量存储设置失败")
                    return False
                
                # 清空现有数据（如果存在）
                try:
                    # 删除现有collection
                    self.vector_store.delete_collection()
                    print("已删除旧的collection")
                    
                    # 重新创建vector_store
                    self.vector_store = Chroma(
                        embedding_function=self.embeddings_model, 
                        persist_directory="./chroma_product_knowledge",
                        collection_name="product_knowledge"
                    )
                    self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
                    print("重新创建向量存储成功")
                    
                except Exception as e:
                    print(f"清空数据时出错: {str(e)}，继续处理...")
            
            # 加载商品知识
            product_docs = self.load_product_knowledge_from_db()
            
            # 加载外部知识库（可选）
            try:
                external_docs = self.load_knowledge_from_mysql()
                product_docs.extend(external_docs)
            except:
                print("外部知识库不可用，跳过加载")
            
            if not product_docs:
                print("没有找到任何知识文档")
                return False
            
            # 分割文档
            split_docs = self.text_splitter.split_documents(product_docs)
            print(f"分割后得到 {len(split_docs)} 个文档块")
            
            # 确保向量存储可用
            if self.vector_store is None:
                print("向量存储不可用，重新设置...")
                self._setup_vector_store()
                if self.vector_store is None:
                    print("向量存储设置失败")
                    return False
            
            # 添加到向量数据库
            if split_docs:
                try:
                    # 分批添加文档，避免一次性添加过多导致错误
                    batch_size = 50
                    for i in range(0, len(split_docs), batch_size):
                        batch = split_docs[i:i+batch_size]
                        self.vector_store.add_documents(batch)
                        print(f"已添加第 {i//batch_size + 1} 批文档 ({len(batch)} 个)")
                    
                    print("向量数据库构建完成")
                    self.is_initialized = True
                    return True
                    
                except Exception as e:
                    print(f"添加文档到向量数据库失败: {str(e)}")
                    # 重置标志，以便下次重试
                    self.is_initialized = False
                    return False
            else:
                print("没有文档块可以添加")
                return False
                
        except Exception as e:
            print(f"初始化向量数据库失败: {str(e)}")
            return False
    
    def ask_question(self, question, return_source=True):
        """
        问答接口
        
        Args:
            question: 用户问题
            return_source: 是否返回来源文档
        
        Returns:
            dict: 包含答案和来源信息的字典
        """
        try:
            # 确保向量数据库已初始化
            if not self.is_initialized or self.vector_store is None or self.retriever is None:
                print("向量数据库未初始化，正在初始化...")
                init_success = self.initialize_vector_store(force_reload=True)
                if not init_success:
                    return {
                        'answer': '抱歉，知识库初始化失败，无法回答问题。请联系管理员检查系统状态。',
                        'sources': [],
                        'success': False
                    }
            
            # 检查chain是否正常
            if self.retriever is None:
                return {
                    'answer': '抱歉，检索器未正确初始化，无法处理问题。',
                    'sources': [],
                    'success': False
                }
            
            # 重新构建chain（确保使用最新的retriever）
            self.chain = (
                {"question": RunnablePassthrough()}
                | RunnablePassthrough.assign(context=itemgetter("question") | self.retriever)
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            # 获取答案
            answer = self.chain.invoke(question)
            
            result = {
                'answer': answer,
                'success': True
            }
            
            # 如果需要返回来源信息
            if return_source:
                try:
                    # 获取相关文档
                    relevant_docs = self.retriever.get_relevant_documents(question)
                    
                    sources = []
                    for doc in relevant_docs[:3]:  # 只返回前3个最相关的来源
                        source_info = {
                            'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            'metadata': doc.metadata
                        }
                        sources.append(source_info)
                    
                    result['sources'] = sources
                    
                except Exception as e:
                    print(f"获取来源信息失败: {str(e)}")
                    result['sources'] = []
            
            return result
            
        except Exception as e:
            print(f"问答处理失败: {str(e)}")
            
            # 如果是Chroma相关错误，尝试重新初始化
            if "collection" in str(e).lower() or "chroma" in str(e).lower():
                print("检测到向量数据库错误，尝试重新初始化...")
                try:
                    self.is_initialized = False
                    init_success = self.initialize_vector_store(force_reload=True)
                    if init_success:
                        # 重试问答
                        return self.ask_question(question, return_source)
                except Exception as retry_e:
                    print(f"重新初始化失败: {str(retry_e)}")
            
            return {
                'answer': f'抱歉，处理问题时出现错误: {str(e)}。请稍后重试或联系管理员。',
                'sources': [],
                'success': False
            }
    
    def get_similar_questions(self, question, limit=5):
        """获取相似问题"""
        try:
            # 使用向量搜索找到相似内容
            relevant_docs = self.retriever.get_relevant_documents(question)
            
            similar_questions = []
            for doc in relevant_docs[:limit]:
                # 从文档内容中提取可能的问题
                content = doc.page_content
                if 'product_name' in doc.metadata:
                    suggested_question = f"关于 {doc.metadata['product_name']} 的信息"
                    similar_questions.append(suggested_question)
            
            return similar_questions
            
        except Exception as e:
            print(f"获取相似问题失败: {str(e)}")
            return []
    
    def update_knowledge(self, product_id, attribute, value, source_text=""):
        """更新商品知识"""
        try:
            # 获取商品
            product = Products.objects.get(product_id=product_id)
            
            # 创建或更新知识条目
            knowledge, created = ProductKnowledge.objects.get_or_create(
                product=product,
                attribute=attribute,
                defaults={
                    'value': value,
                    'source_text': source_text
                }
            )
            
            if not created:
                knowledge.value = value
                knowledge.source_text = source_text
                knowledge.save()
            
            # 重新初始化向量数据库
            self.initialize_vector_store(force_reload=True)
            
            return True
            
        except Exception as e:
            print(f"更新知识失败: {str(e)}")
            return False
    
    def search_knowledge(self, query, filter_by_category=None, filter_by_brand=None):
        """搜索知识库"""
        try:
            # 使用向量搜索
            relevant_docs = self.retriever.get_relevant_documents(query)
            
            results = []
            for doc in relevant_docs:
                # 应用过滤条件
                if filter_by_category and doc.metadata.get('category') != filter_by_category:
                    continue
                if filter_by_brand and doc.metadata.get('brand') != filter_by_brand:
                    continue
                
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })
            
            return results
            
        except Exception as e:
            print(f"搜索知识库失败: {str(e)}")
            return []

# 创建全局RAG系统实例
rag_system = ProductRAGSystem()

# 测试函数
def test_rag_system():
    """测试RAG系统"""
    try:
        # 初始化向量数据库
        print("正在初始化RAG系统...")
        success = rag_system.initialize_vector_store()
        
        if success:
            print("RAG系统初始化成功！")
            
            # 测试问答
            test_questions = [
                "iPhone 15 Pro有什么特点？",
                "哪些耳机支持主动降噪？",
                "MacBook Pro 14的处理器是什么？"
            ]
            
            for question in test_questions:
                print(f"\n问题: {question}")
                result = rag_system.ask_question(question)
                print(f"回答: {result['answer']}")
                if result['sources']:
                    print(f"来源数量: {len(result['sources'])}")
        else:
            print("RAG系统初始化失败！")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == '__main__':
    test_rag_system()

