from operator import itemgetter  # 用于获取字典中的特定键值（如获取'question'对应的值）
from pathlib import Path  # 用于处理文件路径
import os
from collections import defaultdict

from langchain_chroma import Chroma  # 向量数据库Chroma的接口，用于存储和检索嵌入向量
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.output_parsers import StrOutputParser  # 输出解析器，将LLM输出解析为字符串
from langchain_core.prompts import PromptTemplate  # 提示模板，用于构建给大模型的提示词
from langchain_core.runnables import RunnablePassthrough  # 可运行对象，用于流程中传递数据
from langchain_huggingface import HuggingFaceEmbeddings  # 使用HuggingFace模型生成文本嵌入
from langchain_openai import ChatOpenAI
# 使用OpenAI兼容接口的大模型（这里实际是通义千问）
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 按字符分割文本的工具，用于文档分块

# 初始化大语言模型（LLM），使用阿里云DashScope兼容OpenAI的接口，模型为通义千问-max
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

# 定义知识文件所在的目录
file_dir = Path("my_knowledge")

# 定义文本分割器，每个块大小为500字符，块之间有100字符的重叠
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

# 初始化Chroma向量存储，使用本地嵌入模型，向量数据库存储在"chroma_all_v1"目录
vector_store = Chroma(embedding_function=embeddings_model, persist_directory="./chroma_all_v1")

# 创建检索器，设置每次检索返回最相关的5个文档片段
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# 定义提示模板，用于拼接上下文和用户问题，供大模型回答
prompt_template = PromptTemplate.from_template("""
    你是一个智能问答机器人，根据以下信息回答问题：
    {context}
    问题：{question}
    """)

# 构建RAG（检索增强生成）处理链：
# 1. 输入为{"question": 用户问题}，通过RunnablePassthrough传递
# 2. 使用assign添加context字段，其值为通过retriever检索到的相关文档内容
# 3. 将context与question一起传入prompt_template生成完整的提示
# 4. 将提示传给大模型llm生成回答
# 5. 最后将模型输出解析为字符串
chain = (
        {"question": RunnablePassthrough()}
        | RunnablePassthrough.assign(context=itemgetter("question") | retriever)
        | prompt_template
        | llm
        | StrOutputParser()
)


def scan_files_by_type(directory_path):
    """
    扫描目录中的文件，按文件类型分类
    返回：{文件类型: [文件路径列表]}
    """
    file_types = defaultdict(list)

    if not directory_path.exists():
        print(f"目录 {directory_path} 不存在！")
        return file_types

    for file_path in directory_path.iterdir():
        if file_path.is_file():
            file_extension = file_path.suffix.lower()
            file_types[file_extension].append(file_path)

    return file_types


def load_txt_files(file_paths):
    """加载.txt文件"""
    print(f"正在加载 {len(file_paths)} 个 .txt 文件...")
    docs = []
    for file_path in file_paths:
        try:
            loader = TextLoader(str(file_path), encoding='utf-8')
            docs.extend(loader.load())
            print(f"✓ 已加载: {file_path.name}")
        except Exception as e:
            print(f"✗ 加载失败: {file_path.name} - {str(e)}")
    return docs


def load_pdf_files(file_paths):
    """加载.pdf文件"""
    print(f"正在加载 {len(file_paths)} 个 .pdf 文件...")
    docs = []
    for file_path in file_paths:
        try:
            loader = PyPDFLoader(str(file_path))
            docs.extend(loader.load())
            print(f"✓ 已加载: {file_path.name}")
        except Exception as e:
            print(f"✗ 加载失败: {file_path.name} - {str(e)}")
    return docs


def load_docx_files(file_paths):
    """加载.docx文件"""
    print(f"正在加载 {len(file_paths)} 个 .docx 文件...")
    docs = []
    for file_path in file_paths:
        try:
            loader = Docx2txtLoader(str(file_path))
            docs.extend(loader.load())
            print(f"✓ 已加载: {file_path.name}")
        except Exception as e:
            print(f"✗ 加载失败: {file_path.name} - {str(e)}")
    return docs


def process_all_files():
    """处理所有类型的文件"""
    print("=== RAG全家桶脚本启动 ===")
    print(f"扫描目录: {file_dir}")

    # 扫描文件
    file_types = scan_files_by_type(file_dir)

    if not file_types:
        print("未找到任何文件！")
        return

    print("\n发现的文件类型:")
    for ext, files in file_types.items():
        print(f"  {ext}: {len(files)} 个文件")

    all_docs = []

    # 处理.txt文件
    if '.txt' in file_types:
        txt_docs = load_txt_files(file_types['.txt'])
        all_docs.extend(txt_docs)

    # 处理.pdf文件
    if '.pdf' in file_types:
        pdf_docs = load_pdf_files(file_types['.pdf'])
        all_docs.extend(pdf_docs)

    # 处理.docx文件
    if '.docx' in file_types:
        docx_docs = load_docx_files(file_types['.docx'])
        all_docs.extend(docx_docs)

    # 处理其他文件类型（作为文本文件尝试加载）
    other_extensions = [ext for ext in file_types.keys() if ext not in ['.txt', '.pdf', '.docx']]
    if other_extensions:
        print(f"\n发现其他文件类型: {other_extensions}")
        print("尝试作为文本文件加载...")
        for ext in other_extensions:
            try:
                other_docs = load_txt_files(file_types[ext])
                all_docs.extend(other_docs)
            except:
                print(f"无法加载 {ext} 文件")

    if not all_docs:
        print("没有成功加载任何文档！")
        return

    print(f"\n总共加载了 {len(all_docs)} 个文档")

    # 分割文档
    print("正在分割文档...")
    split_docs = text_splitter.split_documents(all_docs)
    print(f"分割后得到 {len(split_docs)} 个文档块")

    # 添加到向量数据库
    print("正在添加到向量数据库...")
    vector_store.add_documents(split_docs)
    print("✓ 向量数据库构建完成！")


if __name__ == '__main__':
    # 处理所有文件
    process_all_files()

    print("\n=== 开始问答测试 ===")

    # 测试问题列表
    test_questions = ["跨部门项目需联系哪个接口人？"]

    for i, question in enumerate(test_questions, 1):
        print(f"\n问题 {i}: {question}")
        print("-" * 50)
        try:
            answer = chain.invoke(question)
            print(f"回答: {answer}")
        except Exception as e:
            print(f"回答出错: {str(e)}")
        print("-" * 50)