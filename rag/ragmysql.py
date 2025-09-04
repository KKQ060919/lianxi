from operator import itemgetter  # 用于获取字典中的特定键值
import pymysql  # MySQL数据库连接器

from langchain_chroma import Chroma  # 向量数据库Chroma的接口
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.output_parsers import StrOutputParser  # 输出解析器
from langchain_core.prompts import PromptTemplate  # 提示模板
from langchain_core.runnables import RunnablePassthrough  # 数据传递组件
from langchain_openai import ChatOpenAI  # OpenAI兼容的大模型接口
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 文本分割器
from langchain_core.documents import Document  # 文档类

# 初始化大语言模型（LLM）
llm = ChatOpenAI(
    api_key="sk-5e387f862dd94499955b83ffe78c722c",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-max"
)

# 初始化文本嵌入模型
embeddings_model = DashScopeEmbeddings(
    model="text-embedding-v3",
    dashscope_api_key="sk-8869c2ac51c5466185e6e39faefff6db"
)

# 定义文本分割器
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

# 初始化Chroma向量存储
vector_store = Chroma(embedding_function=embeddings_model, persist_directory="./chroma_mysql_v1")

# 创建检索器
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# 定义提示模板
prompt_template = PromptTemplate.from_template("""
    你是一个智能问答机器人，根据以下信息回答问题：
    {context}
    问题：{question}
    """)

# 构建RAG处理链
chain = (
        {"question": RunnablePassthrough()}
        | RunnablePassthrough.assign(context=itemgetter("question") | retriever)
        | prompt_template
        | llm
        | StrOutputParser()
)


def load_mysql_data():
    """从MySQL加载数据"""
    # 连接数据库
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

    try:
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
                    # 创建Document对象
                    doc = Document(
                        page_content=row['content_detail'],
                        metadata={
                            'parent_category': row['parent_category'] or "未分类",
                            'child_category': row['child_category'] or "未分类"
                        }
                    )
                    documents.append(doc)

    finally:
        connection.close()

    return documents


if __name__ == '__main__':
    # 加载MySQL数据
    docs = load_mysql_data()
    print(f"从数据库加载了 {len(docs)} 个文档")

    # 分割文档
    split_docs = text_splitter.split_documents(docs)
    print(f"分割后得到 {len(split_docs)} 个文档块")

    # 添加到向量数据库
    vector_store.add_documents(split_docs)
    print("向量数据库构建完成")

    # 测试问答
    question = "为什么要读书？"
    answer = chain.invoke(question)
    print(f"\n问题: {question}")
    print(f"回答: {answer}")